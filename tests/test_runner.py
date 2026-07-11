from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, call, patch

from nixbench.runner import _read_score, _run_shell_command, run_task, write_summary
from nixbench.task import load_task


class RunnerTests(unittest.TestCase):
    def test_reference_solution_passes_and_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            results_dir = root / "results"

            result = run_task(
                task,
                results_dir=results_dir,
                run_id="unit",
                solution_mode="reference",
                keep_workdir=False,
            )

            self.assertTrue(result.passed)
            self.assertEqual(result.score, 10)
            self.assertTrue((results_dir / "unit" / "toy" / "result.json").exists())
            self.assertTrue((results_dir / "unit" / "toy" / "check.log").exists())
            self.assertTrue((results_dir / "unit" / "toy" / "diff.patch").exists())
            self.assertIsNone(result.workdir)
            result_payload = json.loads((results_dir / "unit" / "toy" / "result.json").read_text())
            self.assertEqual(result_payload["task_id"], "toy")
            self.assertTrue(result_payload["passed"])
            self.assertEqual(result_payload["score"], 10)
            self.assertIn("+reference", (results_dir / "unit" / "toy" / "diff.patch").read_text())

    def test_starter_solution_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="starter",
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)

    def test_agent_environment_does_not_expose_hidden_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd=(
                    "python3 -c 'import json, os, pathlib; "
                    'keys=["NIXBENCH_TASK_ID","NIXBENCH_TASK_DIR","NIXBENCH_WORKDIR",'
                    '"NIXBENCH_PROMPT","NIXBENCH_SCORE_FILE"]; '
                    'pathlib.Path("agent-env.json").write_text('
                    "json.dumps({key: os.environ.get(key) for key in keys}, sort_keys=True))'"
                ),
                keep_workdir=True,
                extra_env={
                    "NIXBENCH_TASK_DIR": "/should/not/leak",
                    "NIXBENCH_SCORE_FILE": "/should/not/leak.json",
                },
            )

            self.assertIsNotNone(result.workdir)
            workdir = Path(result.workdir)
            self.addCleanup(shutil.rmtree, workdir.parent, True)
            env = json.loads((workdir / "agent-env.json").read_text())
            self.assertEqual(env["NIXBENCH_TASK_ID"], "toy")
            self.assertIsNone(env["NIXBENCH_TASK_DIR"])
            self.assertIsNone(env["NIXBENCH_SCORE_FILE"])
            self.assertEqual(env["NIXBENCH_WORKDIR"], result.workdir)
            self.assertEqual(env["NIXBENCH_PROMPT"], str(workdir / "NIXBENCH_PROMPT.md"))

    def test_evaluator_receives_hidden_paths_and_agent_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root, check_script=env_check_script())

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd="\n".join(
                    [
                        "{",
                        '  if [ -n "${NIXBENCH_TASK_DIR:-}" ]; then echo task_dir_present; else echo task_dir_absent; fi',
                        '  if [ -n "${NIXBENCH_SCORE_FILE:-}" ]; then echo score_file_present; else echo score_file_absent; fi',
                        "} > agent-env.txt",
                        "printf 'reference\\n' > answer.txt",
                    ]
                ),
                extra_env={
                    "NIXBENCH_TASK_DIR": "/should/be/overridden",
                    "NIXBENCH_SCORE_FILE": "/should/be/overridden.json",
                },
            )

            self.assertTrue(result.passed)
            env_report = Path(result.result_dir, "diff.patch").read_text()
            self.assertIn("task_dir_absent", env_report)
            self.assertIn("score_file_absent", env_report)

    def test_agent_written_score_file_is_removed_before_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            results_dir = root / "results"
            score_file = (results_dir / "unit" / "toy" / "score.json").resolve()

            result = run_task(
                task,
                results_dir=results_dir,
                run_id="unit",
                solution_mode="agent",
                agent_cmd='printf \'{"score":10}\n\' > "$FORGED_SCORE_FILE"',
                extra_env={"FORGED_SCORE_FILE": str(score_file)},
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)
            self.assertIsNone(result.score_detail)

    def test_relative_results_dir_supports_evaluator_score_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_partial_score_task(root, score=7)
            old_cwd = Path.cwd()
            os.chdir(root)
            try:
                result = run_task(
                    task,
                    results_dir=Path("results"),
                    run_id="unit",
                    solution_mode="starter",
                )
            finally:
                os.chdir(old_cwd)

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 7)
            self.assertEqual(result.score_detail, {"score": 7})

    def test_agent_timeout_prevents_default_full_credit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd="printf 'reference\\n' > answer.txt; sleep 2",
                agent_timeout_seconds=1,
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)
            self.assertIsNotNone(result.agent)
            self.assertTrue(result.agent.timed_out)
            self.assertEqual(result.check.returncode, 0)

    def test_evaluator_score_file_is_clamped_to_task_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            high_score = make_toy_task(
                root / "high",
                check_script='set -eu\nprintf \'{"score": 999}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )
            negative_score = make_toy_task(
                root / "negative",
                check_script='set -eu\nprintf \'{"score": -5}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )

            high_result = run_task(
                high_score,
                results_dir=root / "results",
                run_id="high",
                solution_mode="starter",
            )
            negative_result = run_task(
                negative_score,
                results_dir=root / "results",
                run_id="negative",
                solution_mode="starter",
            )

            self.assertFalse(high_result.passed)
            self.assertEqual(high_result.score, 10)
            self.assertFalse(negative_result.passed)
            self.assertEqual(negative_result.score, 0)

    def test_invalid_present_score_files_fail_closed(self) -> None:
        cases = {
            "empty": b"",
            "invalid-utf8": b"\xff",
            "malformed": b"not-json",
            "missing-score": b'{"notes":[]}',
            "boolean": b'{"score":true}',
            "non-finite": b'{"score":NaN}',
            "overflowing-float": b'{"score":1e999}',
            "non-finite-detail": b'{"score":7,"notes":[1e999]}',
            "huge-integer": b'{"score":' + (b"9" * 400) + b"}",
            "numeric-string": b'{"score":"7"}',
            "array": b"[7]",
            "deeply-nested": b'{"score":7,"notes":' + (b"[" * 1_100) + b"0" + (b"]" * 1_100) + b"}",
        }
        with tempfile.TemporaryDirectory() as temp:
            score_file = Path(temp) / "score.json"
            for label, payload in cases.items():
                with self.subTest(case=label):
                    score_file.write_bytes(payload)

                    score, detail, valid = _read_score(score_file, default_score=10, max_score=10)

                    self.assertFalse(valid)
                    self.assertEqual(score, 0)
                    self.assertIsNotNone(detail)
                    self.assertEqual(detail["format"], "invalid")
                    json.dumps(detail, allow_nan=False)

    def test_oversized_score_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            score_file = Path(temp) / "score.json"
            score_file.write_bytes(b" " * 1_000_001)

            score, detail, valid = _read_score(score_file, default_score=10, max_score=10)

            self.assertFalse(valid)
            self.assertEqual(score, 0)
            self.assertEqual(detail, {"format": "invalid", "error": "score file is too large"})

    def test_non_regular_score_paths_fail_closed_without_being_opened(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases = {
                "fifo": root / "score-fifo",
                "symlink": root / "score-link",
            }
            os.mkfifo(cases["fifo"])
            cases["symlink"].symlink_to("/dev/zero")

            for label, score_file in cases.items():
                with self.subTest(case=label):
                    score, detail, valid = _read_score(score_file, default_score=10, max_score=10)

                    self.assertFalse(valid)
                    self.assertEqual(score, 0)
                    self.assertEqual(
                        detail,
                        {"format": "invalid", "error": "score path must be a regular file"},
                    )

    def test_absent_and_valid_score_files_follow_the_score_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            score_file = Path(temp) / "score.json"

            self.assertEqual(_read_score(score_file, default_score=10, max_score=10), (10, None, True))

            score_file.write_text('{"score":7,"notes":["partial"]}')
            score, detail, valid = _read_score(score_file, default_score=10, max_score=10)
            self.assertTrue(valid)
            self.assertEqual(score, 7)
            self.assertEqual(detail, {"score": 7, "notes": ["partial"]})

            score_file.write_text("4")
            self.assertEqual(
                _read_score(score_file, default_score=10, max_score=10),
                (4, {"format": "json-number"}, True),
            )

    def test_invalid_evaluator_score_marks_an_exit_zero_check_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(
                root,
                check_script='set -eu\nprintf \'{"score":NaN}\' > "$NIXBENCH_SCORE_FILE"\nexit 0\n',
            )

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="starter",
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)
            payload = json.loads(Path(result.result_dir, "result.json").read_text())
            self.assertEqual(payload["score_detail"]["format"], "invalid")

    def test_timeout_terminates_descendant_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "survived"
            command = (
                "python3 -c 'import pathlib,time; time.sleep(1.5); "
                f'pathlib.Path("{marker}").write_text("survived")\' & wait'
            )

            result = _run_shell_command(
                command,
                cwd=root,
                env=os.environ.copy(),
                timeout_seconds=1,
                log_path=root / "agent.log",
            )
            time.sleep(0.75)

            self.assertTrue(result.timed_out)
            self.assertEqual(result.returncode, 124)
            self.assertFalse(marker.exists())

    def test_successful_command_does_not_leave_background_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "survived"
            command = (
                "python3 -c 'import pathlib,time; time.sleep(0.3); "
                f'pathlib.Path("{marker}").write_text("survived")\' >/dev/null 2>&1 &'
            )

            result = _run_shell_command(
                command,
                cwd=root,
                env=os.environ.copy(),
                timeout_seconds=5,
                log_path=root / "agent.log",
            )
            time.sleep(0.45)

            self.assertEqual(result.returncode, 0)
            self.assertFalse(result.timed_out)
            self.assertFalse(marker.exists())

    def test_unredirected_background_process_does_not_cause_a_false_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "survived"
            command = (
                "python3 -c 'import pathlib,time; time.sleep(0.3); "
                f'pathlib.Path("{marker}").write_text("survived")\' &'
            )
            started = time.monotonic()

            result = _run_shell_command(
                command,
                cwd=root,
                env=os.environ.copy(),
                timeout_seconds=1,
                log_path=root / "agent.log",
            )
            time.sleep(0.45)

            self.assertEqual(result.returncode, 0)
            self.assertFalse(result.timed_out)
            self.assertLess(time.monotonic() - started, 0.8)
            self.assertFalse(marker.exists())

    def test_timeout_does_not_wait_for_a_detached_pipe_holder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            command = (
                "python3 -c 'import subprocess; "
                'subprocess.Popen(["python3", "-c", "import time; time.sleep(1.5)"], '
                "start_new_session=True)' ; sleep 2"
            )
            started = time.monotonic()

            result = _run_shell_command(
                command,
                cwd=root,
                env=os.environ.copy(),
                timeout_seconds=0.2,
                log_path=root / "agent.log",
            )

            self.assertTrue(result.timed_out)
            self.assertEqual(result.returncode, 124)
            self.assertLess(time.monotonic() - started, 0.8)

    def test_command_logs_replace_invalid_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            log_path = root / "agent.log"

            result = _run_shell_command(
                "python3 -c 'import sys; sys.stdout.buffer.write(bytes([255]))'",
                cwd=root,
                env=os.environ.copy(),
                timeout_seconds=5,
                log_path=log_path,
            )

            self.assertEqual(result.returncode, 0)
            self.assertFalse(result.timed_out)
            self.assertEqual(log_path.read_text(), "\ufffd")

    def test_interruption_terminates_and_reaps_the_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            process = Mock()
            process.wait.side_effect = [KeyboardInterrupt, 0]

            with (
                patch("nixbench.runner.subprocess.Popen", return_value=process),
                patch("nixbench.runner._kill_process_group") as kill_process_group,
                self.assertRaises(KeyboardInterrupt),
            ):
                _run_shell_command(
                    "sleep forever",
                    cwd=root,
                    env=os.environ.copy(),
                    timeout_seconds=5,
                    log_path=root / "agent.log",
                )

            kill_process_group.assert_called_once_with(process)
            self.assertEqual(process.wait.call_args_list, [call(timeout=5), call(timeout=1)])

    def test_write_summary_aggregates_scores_and_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            results_dir = root / "results"
            reference = run_task(
                task,
                results_dir=results_dir,
                run_id="reference",
                solution_mode="reference",
            )
            starter = run_task(
                task,
                results_dir=results_dir,
                run_id="starter",
                solution_mode="starter",
            )

            summary_path = write_summary(results_dir, "combined", [reference, starter])
            summary = json.loads(summary_path.read_text())

            self.assertEqual(summary["passed"], 1)
            self.assertEqual(summary["failed"], 1)
            self.assertEqual(summary["score"], 10)
            self.assertEqual(summary["max_score"], 20)
            self.assertEqual([task["passed"] for task in summary["tasks"]], [True, False])

    def test_diff_artifacts_do_not_follow_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            external = root / "external-secret.txt"
            external.write_text("do-not-copy-into-diff\n")
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd="\n".join(
                    [
                        "printf 'reference\\n' > answer.txt",
                        "printf '\\377\\376\\375' > binary.dat",
                        "python3 -c 'from pathlib import Path; Path(\"large.txt\").write_text(\"x\" * 1000001)'",
                        'ln -s "$EXTERNAL_SECRET" linked.txt',
                    ]
                ),
                extra_env={"EXTERNAL_SECRET": str(external)},
            )

            self.assertTrue(result.passed)
            diff = Path(result.diff_path).read_text()
            self.assertIn("<binary file>", diff)
            self.assertIn("<large file: ", diff)
            self.assertIn("<symlink ->", diff)
            self.assertNotIn("do-not-copy-into-diff", diff)

    def test_diff_records_empty_files_and_final_newline_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            (task.starter_dir / "removed-empty.txt").write_text("")

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd="\n".join(
                    [
                        "rm removed-empty.txt",
                        ": > added-empty.txt",
                        "printf reference > answer.txt",
                    ]
                ),
            )

            self.assertTrue(result.passed)
            diff = Path(result.diff_path).read_text()
            self.assertIn("--- /dev/null\n+++ b/added-empty.txt", diff)
            self.assertIn("--- a/removed-empty.txt\n+++ /dev/null", diff)
            self.assertIn("\\ No newline at end of file", diff)


def make_toy_task(root: Path, *, check_script: str | None = None):
    task_dir = root / "toy"
    (task_dir / "starter").mkdir(parents=True)
    (task_dir / "reference").mkdir()
    (task_dir / "tests").mkdir()

    (task_dir / "prompt.md").write_text("Make answer.txt say reference.\n")
    (task_dir / "starter" / "answer.txt").write_text("starter\n")
    (task_dir / "reference" / "answer.txt").write_text("reference\n")
    (task_dir / "tests" / "check.sh").write_text(check_script or default_check_script())
    (task_dir / "metadata.toml").write_text(
        "\n".join(
            [
                'id = "toy"',
                'name = "Toy"',
                'category = "toy"',
                'difficulty = "easy"',
                "timeout_seconds = 5",
                "max_score = 10",
                'systems = ["any"]',
                'evaluator = "tests/check.sh"',
            ]
        )
        + "\n"
    )

    return load_task(task_dir)


def default_check_script() -> str:
    return (
        "\n".join(
            [
                "set -eu",
                "workdir=${1:-$PWD}",
                'grep -q "^reference$" "$workdir/answer.txt"',
            ]
        )
        + "\n"
    )


def make_partial_score_task(root: Path, *, score: int):
    task_dir = root / "partial"
    (task_dir / "starter").mkdir(parents=True)
    (task_dir / "reference").mkdir()
    (task_dir / "tests").mkdir()

    (task_dir / "prompt.md").write_text("This task always receives partial credit.\n")
    (task_dir / "starter" / "answer.txt").write_text("starter\n")
    (task_dir / "reference" / "answer.txt").write_text("reference\n")
    (task_dir / "tests" / "check.sh").write_text(
        "\n".join(
            [
                "set -eu",
                'mkdir -p "$(dirname "$NIXBENCH_SCORE_FILE")"',
                f'printf \'{{"score":{score}}}\\n\' > "$NIXBENCH_SCORE_FILE"',
                "exit 1",
            ]
        )
        + "\n"
    )
    (task_dir / "metadata.toml").write_text(
        "\n".join(
            [
                'id = "partial"',
                'name = "Partial"',
                'category = "toy"',
                'difficulty = "easy"',
                "timeout_seconds = 5",
                "max_score = 10",
                'systems = ["any"]',
                'evaluator = "tests/check.sh"',
            ]
        )
        + "\n"
    )

    return load_task(task_dir)


def env_check_script() -> str:
    return (
        "\n".join(
            [
                "set -eu",
                "workdir=${1:-$PWD}",
                'test -f "$NIXBENCH_TASK_DIR/metadata.toml"',
                'test -n "$NIXBENCH_SCORE_FILE"',
                'test -f "$NIXBENCH_PROMPT"',
                'grep -q "^task_dir_absent$" "$workdir/agent-env.txt"',
                'grep -q "^score_file_absent$" "$workdir/agent-env.txt"',
                'grep -q "^reference$" "$workdir/answer.txt"',
                'printf \'{"score": 10}\' > "$NIXBENCH_SCORE_FILE"',
            ]
        )
        + "\n"
    )


if __name__ == "__main__":
    unittest.main()
