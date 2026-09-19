from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from nixbench.contracts import (
    candidate_digest,
    contract_result_errors,
    coverage_errors,
    load_contract_cases,
    run_contract_case,
)
from nixbench.task import iter_tasks
from tests.test_runner import make_rubric_task


REPO_ROOT = Path(__file__).resolve().parents[1]


class ContractCaseLoadingTests(unittest.TestCase):
    def test_repository_cases_have_complete_expected_vectors_and_no_known_issues(self) -> None:
        cases = load_contract_cases(
            REPO_ROOT / "contracts", tasks_root=REPO_ROOT / "tasks"
        )
        known_issues = [
            f"{case.task_id}/{case.id}: {case.known_issue}"
            for case in cases
            if case.known_issue is not None
        ]
        self.assertEqual(known_issues, [])
        self.assertTrue(all(case.expected_criteria for case in cases))

    def test_rejects_incomplete_and_extra_expected_vectors(self) -> None:
        for vector, message in (
            ('expected_criteria = {}', "missing evaluates"),
            ('[expected_criteria]\nevaluates = true\nextra = false', "unknown extra"),
        ):
            with self.subTest(vector=vector), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_rubric_task(root / "tasks", exit_code=1, evaluates=False)
                case_root = root / "contracts" / "toy" / "bad-vector"
                (case_root / "candidate").mkdir(parents=True)
                (case_root / "case.toml").write_text(
                    "schema_version = 3\n"
                    'task_id = "toy"\n'
                    'outcome = "reject"\n'
                    'criterion_id = "evaluates"\n'
                    'description = "Bad vector"\n'
                    f"{vector}\n"
                )
                with self.assertRaisesRegex(ValueError, message):
                    load_contract_cases(root / "contracts", tasks_root=root / "tasks")

    def test_rejects_manifest_whose_named_reject_is_expected_true(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_rubric_task(root / "tasks", exit_code=1, evaluates=False)
            case_root = root / "contracts" / "toy" / "mislabeled"
            (case_root / "candidate").mkdir(parents=True)
            (case_root / "case.toml").write_text(
                "schema_version = 3\n"
                'task_id = "toy"\n'
                'outcome = "reject"\n'
                'criterion_id = "evaluates"\n'
                'description = "Mislabeled reject"\n'
                '[expected_criteria]\n'
                'evaluates = true\n'
            )
            with self.assertRaisesRegex(ValueError, "named criterion false"):
                load_contract_cases(root / "contracts", tasks_root=root / "tasks")

    def test_rejects_undocumented_coupled_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_rubric_task(root / "tasks", exit_code=1, evaluates=False)
            metadata = task.root / "metadata.toml"
            metadata.write_text(metadata.read_text().replace("points = 10", "points = 5"))
            with metadata.open("a") as handle:
                handle.write(
                    '\n[[criteria]]\nid = "other"\npoints = 5\nrequired = true\nfailure_class = "evaluation"\n'
                )
            case_root = root / "contracts" / "toy" / "coupled"
            (case_root / "candidate").mkdir(parents=True)
            (case_root / "case.toml").write_text(
                "schema_version = 3\n"
                'task_id = "toy"\n'
                'outcome = "reject"\n'
                'criterion_id = "evaluates"\n'
                'description = "Undocumented coupling"\n'
                '[expected_criteria]\n'
                'evaluates = false\n'
                'other = false\n'
            )
            with self.assertRaisesRegex(ValueError, "undocumented other"):
                load_contract_cases(root / "contracts", tasks_root=root / "tasks")

    def test_rejects_escaping_candidate_operation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_rubric_task(root / "tasks", exit_code=1, evaluates=False)
            case_root = root / "contracts" / "toy" / "escape"
            (case_root / "candidate").mkdir(parents=True)
            (case_root / "case.toml").write_text(
                "schema_version = 3\n"
                'task_id = "toy"\n'
                'outcome = "reject"\n'
                'criterion_id = "evaluates"\n'
                'description = "Escaping delete path"\n'
                'delete = ["../secret"]\n'
                '[expected_criteria]\n'
                'evaluates = false\n'
            )
            with self.assertRaisesRegex(ValueError, "stay inside"):
                load_contract_cases(root / "contracts", tasks_root=root / "tasks")


@unittest.skipIf(shutil.which("nix") is None, "nix is required for evaluator contract tests")
class EvaluatorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = iter_tasks(REPO_ROOT / "tasks")
        cls.cases = load_contract_cases(
            REPO_ROOT / "contracts", tasks_root=REPO_ROOT / "tasks"
        )

    def test_contract_cases_match_complete_vectors_without_evaluator_errors(self) -> None:
        for case in self.cases:
            with self.subTest(task=case.task_id, case=case.id):
                run = run_contract_case(case, repo_root=REPO_ROOT)
                self.assertEqual(contract_result_errors(run), [], run.log)
                self.assertNotIn("error:", run.log.lower(), run.log)

    def test_syntax_invalid_candidate_is_a_valid_all_false_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(
                REPO_ROOT / "tasks" / "module-stale-option-migration",
                root / "tasks" / "module-stale-option-migration",
            )
            case_root = (
                root
                / "contracts"
                / "module-stale-option-migration"
                / "syntax-invalid-module"
            )
            (case_root / "candidate").mkdir(parents=True)
            (case_root / "candidate" / "module.nix").write_text("{\n")
            (case_root / "case.toml").write_text(
                "schema_version = 3\n"
                'task_id = "module-stale-option-migration"\n'
                'outcome = "reject"\n'
                'criterion_id = "sddm-current"\n'
                'description = "Candidate module has invalid Nix syntax"\n'
                '[coupled_failures]\n'
                'plasma-current = "Whole-candidate syntax failure prevents evaluation."\n'
                'graphics-current = "Whole-candidate syntax failure prevents evaluation."\n'
                'kdeconnect-no-stale = "Whole-candidate syntax failure prevents evaluation."\n'
                '[expected_criteria]\n'
                'sddm-current = false\n'
                'plasma-current = false\n'
                'graphics-current = false\n'
                'kdeconnect-no-stale = false\n'
            )
            case = load_contract_cases(
                root / "contracts", tasks_root=root / "tasks"
            )[0]
            run = run_contract_case(case, repo_root=root)
            self.assertEqual(run.result.measurement_status, "valid", run.log)
            self.assertEqual(run.result.check.returncode, 1, run.log)
            self.assertEqual(run.result.criteria, case.expected_criteria, run.log)
            self.assertIn("error:", run.log.lower())

    def test_confirmed_totality_regressions_keep_unrelated_credit(self) -> None:
        expected = {
            "fhs-binary-wrapper/fhs-wrapper-fetches-an-unpinned-empty-source": {
                "appimage-package": True,
                "pinned-source": False,
                "fhs-runtime": True,
                "no-host-mutation": True,
            },
            "flake-per-system-outputs/flake-app-missing-package-metadata": {
                "systems-output": True,
                "packages-and-apps": False,
                "checks-and-shells": True,
                "flake-evaluates": True,
            },
            "home-manager-extra-special-args/home-manager-forwards-only-known-inputs": {
                "nixos-system": True,
                "module-integration": True,
                "forwards-inputs": False,
                "user-imports": True,
            },
            "issue-report-quality/issue-report-missing-expected-behavior": {
                "report-fields": False,
                "reproduction-and-system": True,
                "outcome-evidence": True,
                "bounded-analysis": True,
            },
            "lang-attrsets-normalize/attrset-normalizer-removes-argument-defaults": {
                "names-and-versions": True,
                "by-system": True,
                "default-packages": False,
                "parameterized-systems": True,
            },
            "module-stale-option-migration/retains-stale-option-path": {
                "sddm-current": False,
                "plasma-current": True,
                "graphics-current": True,
                "kdeconnect-no-stale": True,
            },
            "overlay-override-package/overlay-debug-package-bypasses-final": {
                "base-override": True,
                "patch-and-check": True,
                "meta-preservation": True,
                "debug-from-final": False,
            },
            "purity-wrapper-derivation/pure-wrapper-uses-forbidden-get-exe-helper": {
                "derivation-identity": True,
                "wrapper-inputs": True,
                "pure-install-phase": False,
                "purity-marker": True,
            },
        }
        by_key = {(case.task_id, case.id): case for case in self.cases}
        for label, vector in expected.items():
            task_id, case_id = label.split("/", 1)
            with self.subTest(case=label):
                run = run_contract_case(by_key[(task_id, case_id)], repo_root=REPO_ROOT)
                self.assertEqual(run.result.criteria, vector, run.log)
                self.assertNotIn("error:", run.log.lower(), run.log)

    def test_every_required_criterion_has_distinct_targeted_rejection(self) -> None:
        digests = {
            (case.task_id, case.id): candidate_digest(case, repo_root=REPO_ROOT)
            for case in self.cases
        }
        self.assertEqual(
            coverage_errors(self.tasks, self.cases, candidate_digests=digests),
            [],
        )

    def test_coverage_checker_uses_rejects_not_passing_labels(self) -> None:
        task = next(task for task in self.tasks if task.id == "package-stdenv-cli")
        cases = tuple(
            case
            for case in self.cases
            if case.task_id == task.id and case.outcome == "pass"
        )
        errors = coverage_errors([task], cases)
        self.assertIn("package-stdenv-cli: missing reject contract case", errors)
        self.assertTrue(
            any("missing targeted rejecting fixture" in error for error in errors),
            errors,
        )

    def test_duplicate_rejecting_candidates_are_not_independent_evidence(self) -> None:
        task = next(task for task in self.tasks if task.id == "debug-network-false-lead")
        reject = next(
            case
            for case in self.cases
            if case.task_id == task.id and case.outcome == "reject"
        )
        cases = (reject, reject)
        digests = {(reject.task_id, reject.id): "same"}
        errors = coverage_errors([task], cases, candidate_digests=digests)
        self.assertTrue(any("duplicate rejecting candidate digest" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
