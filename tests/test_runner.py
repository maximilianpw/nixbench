from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nixbench.runner import make_run_id, run_task
from nixbench.task import load_task


class RunnerTests(unittest.TestCase):
    def test_run_ids_are_unique(self) -> None:
        self.assertNotEqual(make_run_id(), make_run_id())

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

    def test_agent_does_not_receive_hidden_evaluator_environment(self) -> None:
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
            )

            self.assertTrue(result.passed)
            env_report = Path(result.result_dir, "diff.patch").read_text()
            self.assertIn("task_dir_absent", env_report)
            self.assertIn("score_file_absent", env_report)

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

    def test_agent_cannot_forge_score_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root, check_script="set -eu\nexit 1\n")

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd='if [ -n "${NIXBENCH_SCORE_FILE:-}" ]; then printf "10" > "$NIXBENCH_SCORE_FILE"; fi',
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)

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
