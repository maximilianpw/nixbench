from __future__ import annotations

import math
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from nixbench.runner import run_task
from nixbench.task import find_task, iter_tasks


REPO_ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(shutil.which("nix") is None, "nix is required for corpus evaluator tests")
class CorpusHealthTests(unittest.TestCase):
    def test_bundled_evaluators_exit_from_required_criteria(self) -> None:
        for task in iter_tasks(REPO_ROOT / "tasks"):
            with self.subTest(task=task.id):
                source = task.evaluator_path.read_text()
                self.assertIn("NIXBENCH_EVALUATOR_EXIT", source)
                self.assertNotIn('all(json.load(open(sys.argv[1]))["criteria"].values())', source)
                self.assertNotIn("all(criteria.values())", source)

    def test_flake_evaluation_criterion_does_not_repeat_output_assertions(self) -> None:
        source = (
            REPO_ROOT / "tasks" / "flake-per-system-outputs" / "tests" / "check.sh"
        ).read_text()
        criterion = source.split('"flake-evaluates" = passes (', 1)[1].split(
            ");", 1
        )[0]

        self.assertIn("flake.inputs", criterion)
        self.assertIn("flakeAttempt.success", criterion)
        self.assertIn("outputsAttempt.success", criterion)
        for overlapping_name in ("packages", "apps", "checks", "devShells", "checkSystem"):
            self.assertNotIn(overlapping_name, criterion)

    def test_every_task_uses_a_bounded_structured_rubric(self) -> None:
        for task in iter_tasks(REPO_ROOT / "tasks"):
            with self.subTest(task=task.id):
                self.assertEqual(task.scoring_schema, "criteria-v2")
                self.assertGreaterEqual(len(task.criteria), 4)
                self.assertLessEqual(len(task.criteria), 8)

    def test_nushell_evaluator_does_not_depend_on_ambient_name(self) -> None:
        task = find_task(REPO_ROOT / "tasks", "nushell-command-not-found")
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ):
            os.environ.pop("name", None)
            result = run_task(
                task,
                results_dir=Path(temp) / "results",
                run_id="nushell-without-name",
                solution_mode="reference",
            )

            check_log = Path(result.check.log_path).read_text()
            self.assertTrue(result.passed, check_log)

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
                    self.assertEqual(result.measurement_status, "valid", check_log)
                    self.assertEqual(result.task_outcome, "pass", check_log)
                    self.assertEqual(result.scoring_schema, "criteria-v2", check_log)
                    self.assertTrue(all(result.criteria.values()), check_log)
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
                    self.assertEqual(result.measurement_status, "valid", check_log)
                    self.assertEqual(result.task_outcome, "fail", check_log)
                    self.assertEqual(result.scoring_schema, "criteria-v2", check_log)
                    self.assertTrue(result.criteria, check_log)
                    self.assertFalse(all(result.criteria.values()), check_log)
                    self.assertTrue(result.score_valid, check_log)
                    self.assertFalse(result.check.timed_out, check_log)
                    self.assertEqual(result.check.returncode, 1, check_log)
                    self.assertTrue(math.isfinite(result.score), check_log)
                    self.assertGreaterEqual(result.score, 0, check_log)
                    self.assertLess(result.score, task.max_score, check_log)


if __name__ == "__main__":
    unittest.main()
