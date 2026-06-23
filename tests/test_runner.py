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


if __name__ == "__main__":
    unittest.main()
