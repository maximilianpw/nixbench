from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from nixbench.task import iter_tasks
from tests.evaluator_contracts import (
    coverage_errors,
    load_contract_cases,
    run_contract_case,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContractCaseLoadingTests(unittest.TestCase):
    def test_repository_cases_have_no_known_evaluator_issues(self) -> None:
        cases = load_contract_cases(
            REPO_ROOT / "contracts", tasks_root=REPO_ROOT / "tasks"
        )
        known_issues = [
            f"{case.task_id}/{case.id}: {case.known_issue}"
            for case in cases
            if case.known_issue is not None
        ]
        self.assertEqual(known_issues, [])

    def test_rejects_malformed_and_escaping_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tasks = root / "tasks"
            (tasks / "toy").mkdir(parents=True)
            case_root = root / "contracts" / "toy" / "escape"
            (case_root / "candidate").mkdir(parents=True)
            (case_root / "case.toml").write_text(
                """schema_version = 2
task_id = "toy"
outcome = "pass"
criterion_id = "path-safety"
description = "Escaping delete path"
delete = ["../secret"]
"""
            )

            with self.assertRaisesRegex(ValueError, "stay inside"):
                load_contract_cases(root / "contracts", tasks_root=tasks)

    def test_rejects_unknown_outcome_and_mismatched_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tasks = root / "tasks"
            (tasks / "toy").mkdir(parents=True)
            case_root = root / "contracts" / "toy" / "bad"
            (case_root / "candidate").mkdir(parents=True)
            manifest = case_root / "case.toml"
            manifest.write_text(
                """schema_version = 2
task_id = "other"
outcome = "maybe"
criterion_id = "loader"
description = "Invalid fields"
"""
            )

            with self.assertRaisesRegex(ValueError, "task_id does not match"):
                load_contract_cases(root / "contracts", tasks_root=tasks)


@unittest.skipIf(shutil.which("nix") is None, "nix is required for evaluator contract tests")
class EvaluatorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = load_contract_cases(
            REPO_ROOT / "contracts", tasks_root=REPO_ROOT / "tasks"
        )

    def test_contract_cases(self) -> None:
        for case in self.cases:
            with self.subTest(task=case.task_id, case=case.id):
                if case.known_issue is not None:
                    self.skipTest(f"known_issue={case.known_issue}: {case.description}")
                result, log = run_contract_case(case, repo_root=REPO_ROOT)
                if case.outcome == "pass":
                    self.assertTrue(
                        result.passed, f"{case.task_id}/{case.id} failed:\n{log}"
                    )
                    self.assertTrue(result.criteria[case.criterion_id], log)
                else:
                    self.assertFalse(
                        result.passed, f"{case.task_id}/{case.id} passed:\n{log}"
                    )
                    self.assertTrue(result.score_valid, log)
                    self.assertFalse(result.check.timed_out, log)
                    self.assertEqual(result.check.returncode, 1, log)
                    self.assertFalse(result.criteria[case.criterion_id], log)

    def test_per_system_output_failure_keeps_flake_evaluation_credit(self) -> None:
        case = next(
            case
            for case in self.cases
            if case.task_id == "flake-per-system-outputs"
            and case.id == "output-specific-miss-is-isolated"
        )

        result, log = run_contract_case(case, repo_root=REPO_ROOT)

        self.assertEqual(result.measurement_status, "valid", log)
        self.assertEqual(
            result.criteria,
            {
                "systems-output": True,
                "packages-and-apps": False,
                "checks-and-shells": True,
                "flake-evaluates": True,
            },
            log,
        )

    def test_default_input_selection_loses_only_named_output_credit(self) -> None:
        case = next(
            case
            for case in self.cases
            if case.task_id == "flake-input-package-selection"
            and case.id == "uses-default-flake-package"
        )

        result, log = run_contract_case(case, repo_root=REPO_ROOT)

        self.assertEqual(result.measurement_status, "valid", log)
        self.assertEqual(
            result.criteria,
            {
                "linux-packages": True,
                "darwin-packages": True,
                "named-input-output": False,
                "package-values": True,
            },
            log,
        )

    def test_every_task_has_pass_and_reject_cases(self) -> None:
        tasks = iter_tasks(REPO_ROOT / "tasks")
        task_ids = {task.id for task in tasks}
        required_criteria = {
            task.id: {
                criterion.id for criterion in task.criteria if criterion.required
            }
            for task in tasks
        }
        self.assertEqual(
            coverage_errors(
                task_ids, self.cases, required_criteria=required_criteria
            ),
            [],
        )

    def test_completeness_checker_names_missing_outcome(self) -> None:
        cases = tuple(
            case
            for case in self.cases
            if not (case.task_id == "package-stdenv-cli" and case.outcome == "pass")
        )
        self.assertEqual(
            coverage_errors({"package-stdenv-cli"}, cases),
            ["package-stdenv-cli: missing pass contract case"],
        )


if __name__ == "__main__":
    unittest.main()
