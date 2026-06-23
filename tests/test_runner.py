from __future__ import annotations

import json
import os
import shutil
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

    def test_agent_written_score_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd=(
                    'if [ -n "${NIXBENCH_SCORE_FILE:-}" ]; then '
                    'printf \'{"score":100,"notes":["agent wrote score file"]}\\n\' > "$NIXBENCH_SCORE_FILE"; '
                    "fi"
                ),
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

    def test_evaluator_score_is_clamped_to_task_max(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_partial_score_task(root, score=999)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="starter",
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 10)

    def test_agent_timeout_fails_even_if_workdir_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="unit",
                solution_mode="agent",
                agent_cmd="printf 'reference\n' > answer.txt; sleep 2",
                agent_timeout_seconds=1,
            )

            self.assertFalse(result.passed)
            self.assertEqual(result.score, 0)
            self.assertIsNotNone(result.agent)
            self.assertTrue(result.agent.timed_out)


def make_toy_task(root: Path):
    task_dir = root / "toy"
    (task_dir / "starter").mkdir(parents=True)
    (task_dir / "reference").mkdir()
    (task_dir / "tests").mkdir()

    (task_dir / "prompt.md").write_text("Make answer.txt say reference.\n")
    (task_dir / "starter" / "answer.txt").write_text("starter\n")
    (task_dir / "reference" / "answer.txt").write_text("reference\n")
    (task_dir / "tests" / "check.sh").write_text(
        "\n".join(
            [
                "set -eu",
                "workdir=${1:-$PWD}",
                'grep -q "^reference$" "$workdir/answer.txt"',
            ]
        )
        + "\n"
    )
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


if __name__ == "__main__":
    unittest.main()
