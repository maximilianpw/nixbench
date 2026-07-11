from __future__ import annotations

import math
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
        tasks = iter_tasks(REPO_ROOT / "tasks")
        self.assertGreater(len(tasks), 0, "the benchmark corpus must not be empty")
        with tempfile.TemporaryDirectory() as temp:
            results_dir = Path(temp) / "results"
            for task in tasks:
                result = run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"reference-{task.id}",
                    solution_mode="reference",
                )
                with self.subTest(task=task.id):
                    check_log = Path(result.check.log_path).read_text()
                    self.assertTrue(result.passed, check_log)
                    self.assertEqual(result.score, task.max_score, check_log)

    def test_starter_solutions_fail(self) -> None:
        tasks = iter_tasks(REPO_ROOT / "tasks")
        self.assertGreater(len(tasks), 0, "the benchmark corpus must not be empty")
        with tempfile.TemporaryDirectory() as temp:
            results_dir = Path(temp) / "results"
            for task in tasks:
                result = run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"starter-{task.id}",
                    solution_mode="starter",
                )
                with self.subTest(task=task.id):
                    check_log = Path(result.check.log_path).read_text()
                    self.assertFalse(result.passed, check_log)
                    self.assertTrue(result.score_valid, check_log)
                    self.assertFalse(result.check.timed_out, check_log)
                    self.assertEqual(result.check.returncode, 1, check_log)
                    self.assertTrue(math.isfinite(result.score), check_log)
                    self.assertGreaterEqual(result.score, 0, check_log)
                    self.assertLess(result.score, task.max_score, check_log)


if __name__ == "__main__":
    unittest.main()
