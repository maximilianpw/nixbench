from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from nixbench.runner import run_task
from nixbench.task import iter_tasks


REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(shutil.which("nix") is None, "nix is required for corpus evaluator tests")
class CorpusHealthTests(unittest.TestCase):
    def test_reference_solutions_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            results_dir = Path(temp) / "results"
            failures = []

            for task in iter_tasks(REPO_ROOT / "tasks"):
                result = run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"reference-{task.id}",
                    solution_mode="reference",
                )
                if not result.passed:
                    failures.append(task.id)

            self.assertEqual(failures, [])

    def test_starter_solutions_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            results_dir = Path(temp) / "results"
            unexpected_passes = []

            for task in iter_tasks(REPO_ROOT / "tasks"):
                result = run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"starter-{task.id}",
                    solution_mode="starter",
                )
                if result.passed:
                    unexpected_passes.append(task.id)

            self.assertEqual(unexpected_passes, [])


if __name__ == "__main__":
    unittest.main()
