from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from nixbench.cli import main
from tests.test_runner import make_toy_task


class CliTests(unittest.TestCase):
    def test_validate_accepts_failing_starter_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_passing_starter_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root, check_script="exit 0\n")

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_accepts_passing_reference_solution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "reference",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 reference outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_an_under_scored_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":5}\' > "$NIXBENCH_SCORE_FILE"\nexit 0\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "reference",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 reference outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_full_scored_starter_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":10}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_accepts_a_partial_scored_starter_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":5}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_timed_out_starter_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root, check_script="sleep 2\n")
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(metadata_path.read_text().replace("timeout_seconds = 5", "timeout_seconds = 1"))

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_an_invalid_starter_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":NaN}\' > "$NIXBENCH_SCORE_FILE"\nexit 0\n',
            )

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_starter_evaluator_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root, check_script="exit 2\n")

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_run_all_rejects_an_empty_task_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            returncode, stdout, stderr = run_cli(root, "run-all", "--solution", "starter")

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("error: no tasks", stderr)

    def test_execution_rejects_a_results_directory_inside_the_task_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                root / "results",
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("--results-dir must be outside --tasks-dir", stderr)

    def test_run_all_rejects_an_empty_system_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(
                metadata_path.read_text().replace('systems = ["any"]', 'systems = ["x86_64-linux"]')
            )

            returncode, stdout, stderr = run_cli(
                root,
                "--system",
                "aarch64-darwin",
                "run-all",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("support system aarch64-darwin", stderr)

    def test_run_rejects_an_unsupported_task_without_reporting_a_skip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(
                metadata_path.read_text().replace('systems = ["any"]', 'systems = ["x86_64-linux"]')
            )

            returncode, stdout, stderr = run_cli(
                root,
                "--system",
                "aarch64-darwin",
                "run",
                "toy",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("no task was run", stderr)

    def test_run_all_repeats_trials_and_writes_a_study_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "2",
                "--model",
                "toy-model",
                "--effort",
                "high",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("trial 1/2", stdout)
            self.assertIn("trial 2/2", stdout)
            self.assertEqual(stderr, "")
            study_paths = list((results_dir / "studies").glob("*/summary.json"))
            self.assertEqual(len(study_paths), 1)
            study = json.loads(study_paths[0].read_text())
            self.assertEqual(study["trial_count"], 2)
            self.assertEqual(study["metadata"]["model"], "toy-model")
            self.assertEqual(study["metadata"]["effort"], "high")

    def test_run_all_rejects_zero_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "0",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("--trials must be at least 1", stderr)

    def test_repeated_study_stops_on_agent_infrastructure_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--agent-cmd",
                "exit 7",
                "--trials",
                "2",
            )

            self.assertEqual(returncode, 2)
            self.assertIn("trial 1/2", stdout)
            self.assertIn("agent command exited 7", stderr)
            self.assertFalse((results_dir / "studies").exists())

    def test_study_count_prints_completed_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)
            returncode, _, _ = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "2",
                "--series",
                "toy",
                "--effort",
                "high",
            )
            self.assertEqual(returncode, 0)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "study-count",
                "--series",
                "toy",
                "--effort",
                "high",
                "--task-count",
                "1",
            )

            self.assertEqual(returncode, 0)
            self.assertEqual(stdout, "2\n")
            self.assertEqual(stderr, "")

    def test_repeated_study_checkpoints_valid_trials_before_a_later_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            counter = root / "agent-count"
            make_toy_task(root)
            agent_cmd = (
                f'count=$(cat "{counter}" 2>/dev/null || printf 0); '
                'count=$((count + 1)); '
                f'printf "%s" "$count" > "{counter}"; '
                'if [ "$count" -eq 1 ]; then printf "reference\\n" > answer.txt; exit 0; fi; '
                'exit 7'
            )

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--agent-cmd",
                agent_cmd,
                "--trials",
                "2",
                "--series",
                "toy",
                "--effort",
                "high",
            )

            self.assertEqual(returncode, 2)
            self.assertIn("study checkpoint: 1/2", stdout)
            self.assertIn("agent command exited 7", stderr)
            study_paths = list((results_dir / "studies").glob("*/summary.json"))
            self.assertEqual(len(study_paths), 1)
            study = json.loads(study_paths[0].read_text())
            self.assertEqual(study["trial_count"], 1)


def run_cli(tasks_dir: Path, *args: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as results:
        return invoke_cli(tasks_dir, Path(results), *args)


def invoke_cli(tasks_dir: Path, results_dir: Path, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = [
        "--tasks-dir",
        str(tasks_dir),
        "--results-dir",
        str(results_dir),
        *args,
    ]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        returncode = main(argv)
    return returncode, stdout.getvalue(), stderr.getvalue()


if __name__ == "__main__":
    unittest.main()
