from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from .runner import TaskRunResult, run_task
from .task import TASK_ID_PATTERN, Task, load_task


VALID_OUTCOMES = {"pass", "reject"}
CONTRACT_SCHEMA_VERSION = 3


@dataclass(frozen=True)
class RenameOperation:
    source: PurePosixPath
    destination: PurePosixPath


@dataclass(frozen=True)
class EvaluatorContractCase:
    id: str
    task_id: str
    outcome: str
    criterion_id: str
    description: str
    expected_criteria: dict[str, bool]
    coupled_failures: dict[str, str]
    root: Path
    candidate_dir: Path
    delete: tuple[PurePosixPath, ...]
    rename: tuple[RenameOperation, ...]
    known_issue: str | None
    duplicate_candidate_reason: str | None


@dataclass(frozen=True)
class ContractRun:
    case: EvaluatorContractCase
    result: TaskRunResult
    log: str
    candidate_digest: str


def load_contract_cases(
    contracts_root: Path, *, tasks_root: Path
) -> tuple[EvaluatorContractCase, ...]:
    contracts_root = contracts_root.resolve()
    tasks_root = tasks_root.resolve()
    if not contracts_root.is_dir():
        raise ValueError(f"contracts root does not exist: {contracts_root}")
    if not tasks_root.is_dir():
        raise ValueError(f"tasks root does not exist: {tasks_root}")

    known_tasks = {path.name for path in tasks_root.iterdir() if path.is_dir()}
    task_criteria: dict[str, set[str]] = {}
    for task_id in known_tasks:
        if (tasks_root / task_id / "metadata.toml").is_file():
            task = load_task(tasks_root / task_id)
            task_criteria[task_id] = {criterion.id for criterion in task.criteria}

    cases: list[EvaluatorContractCase] = []
    seen: set[tuple[str, str]] = set()
    for manifest_path in sorted(contracts_root.glob("*/*/case.toml")):
        case_root = manifest_path.parent
        task_dir_id = case_root.parent.name
        case_id = case_root.name
        if TASK_ID_PATTERN.fullmatch(task_dir_id) is None:
            raise ValueError(f"invalid contract task directory ID: {task_dir_id}")
        if TASK_ID_PATTERN.fullmatch(case_id) is None:
            raise ValueError(f"invalid contract case ID: {case_id}")
        if task_dir_id not in known_tasks:
            raise ValueError(f"contract case references unknown task: {task_dir_id}")
        try:
            with manifest_path.open("rb") as handle:
                data = tomllib.load(handle)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(f"cannot read contract case {manifest_path}: {exc}") from exc

        required = {
            "schema_version",
            "task_id",
            "outcome",
            "criterion_id",
            "description",
            "expected_criteria",
        }
        optional = {
            "delete",
            "rename",
            "known_issue",
            "coupled_failures",
            "duplicate_candidate_reason",
        }
        missing = sorted(required - data.keys())
        unknown = sorted(data.keys() - required - optional)
        if missing:
            raise ValueError(f"{manifest_path}: missing fields: {', '.join(missing)}")
        if unknown:
            raise ValueError(f"{manifest_path}: unknown fields: {', '.join(unknown)}")
        if type(data["schema_version"]) is not int or data["schema_version"] != CONTRACT_SCHEMA_VERSION:
            raise ValueError(
                f"{manifest_path}: schema_version must be {CONTRACT_SCHEMA_VERSION}"
            )
        if data["task_id"] != task_dir_id:
            raise ValueError(f"{manifest_path}: task_id does not match its directory")
        outcome = data["outcome"]
        if outcome not in VALID_OUTCOMES:
            raise ValueError(f"{manifest_path}: outcome must be pass or reject")
        for field in ("criterion_id", "description"):
            if not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"{manifest_path}: {field} must be nonempty")

        declared_criteria = task_criteria.get(task_dir_id, set())
        criterion_id = data["criterion_id"]
        if criterion_id not in declared_criteria:
            raise ValueError(
                f"{manifest_path}: criterion_id is not declared by task {task_dir_id}"
            )
        expected_criteria = _boolean_table(
            data["expected_criteria"], f"{manifest_path}: expected_criteria"
        )
        missing_criteria = sorted(declared_criteria - expected_criteria.keys())
        extra_criteria = sorted(expected_criteria.keys() - declared_criteria)
        if missing_criteria or extra_criteria:
            details: list[str] = []
            if missing_criteria:
                details.append(f"missing {', '.join(missing_criteria)}")
            if extra_criteria:
                details.append(f"unknown {', '.join(extra_criteria)}")
            raise ValueError(
                f"{manifest_path}: expected_criteria must exactly match task criteria ({'; '.join(details)})"
            )
        if outcome == "pass" and not all(expected_criteria.values()):
            raise ValueError(f"{manifest_path}: passing fixture must expect every criterion true")
        if outcome == "reject" and expected_criteria[criterion_id]:
            raise ValueError(
                f"{manifest_path}: rejecting fixture must expect named criterion false"
            )

        coupled_failures = _string_table(
            data.get("coupled_failures", {}), f"{manifest_path}: coupled_failures"
        )
        expected_coupled = {
            key
            for key, value in expected_criteria.items()
            if not value and key != criterion_id
        }
        if set(coupled_failures) != expected_coupled:
            missing_coupled = sorted(expected_coupled - coupled_failures.keys())
            extra_coupled = sorted(coupled_failures.keys() - expected_coupled)
            details = []
            if missing_coupled:
                details.append(f"undocumented {', '.join(missing_coupled)}")
            if extra_coupled:
                details.append(f"not expected false {', '.join(extra_coupled)}")
            raise ValueError(
                f"{manifest_path}: coupled_failures must document exactly the unrelated false criteria ({'; '.join(details)})"
            )

        known_issue = _optional_nonempty_string(data.get("known_issue"), manifest_path, "known_issue")
        duplicate_reason = _optional_nonempty_string(
            data.get("duplicate_candidate_reason"), manifest_path, "duplicate_candidate_reason"
        )
        delete = tuple(
            _safe_relative_path(value, f"{manifest_path}: delete")
            for value in _string_list(data.get("delete", []), f"{manifest_path}: delete")
        )
        rename_data = data.get("rename", [])
        if not isinstance(rename_data, list):
            raise ValueError(f"{manifest_path}: rename must be an array of tables")
        rename: list[RenameOperation] = []
        for operation in rename_data:
            if not isinstance(operation, dict) or set(operation) != {"from", "to"}:
                raise ValueError(f"{manifest_path}: each rename needs from and to")
            rename.append(
                RenameOperation(
                    _safe_relative_path(operation["from"], f"{manifest_path}: rename.from"),
                    _safe_relative_path(operation["to"], f"{manifest_path}: rename.to"),
                )
            )
        candidate_dir = case_root / "candidate"
        if not candidate_dir.is_dir():
            raise ValueError(f"{manifest_path}: missing candidate directory")
        key = (task_dir_id, case_id)
        if key in seen:
            raise ValueError(f"duplicate contract case ID: {task_dir_id}/{case_id}")
        seen.add(key)
        cases.append(
            EvaluatorContractCase(
                id=case_id,
                task_id=task_dir_id,
                outcome=outcome,
                criterion_id=criterion_id,
                description=data["description"],
                expected_criteria=expected_criteria,
                coupled_failures=coupled_failures,
                root=case_root,
                candidate_dir=candidate_dir,
                delete=delete,
                rename=tuple(rename),
                known_issue=known_issue,
                duplicate_candidate_reason=duplicate_reason,
            )
        )
    return tuple(cases)


def run_contract_case(
    case: EvaluatorContractCase,
    *,
    repo_root: Path,
    results_dir: Path | None = None,
    run_id: str | None = None,
) -> ContractRun:
    repo_root = repo_root.resolve()
    with tempfile.TemporaryDirectory(prefix="nixbench-contract-") as temp:
        root = Path(temp)
        task_root = root / "tasks" / case.task_id
        shutil.copytree(repo_root / "tasks" / case.task_id, task_root, symlinks=True)
        starter = task_root / "starter"
        apply_contract_candidate(case, starter)
        digest = tree_digest(starter)
        task = load_task(task_root)
        result = run_task(
            task,
            results_dir=results_dir or root / "results",
            run_id=run_id or f"{case.task_id}-{case.id}",
            solution_mode="starter",
        )
        return ContractRun(
            case=case,
            result=result,
            log=Path(result.check.log_path).read_text(),
            candidate_digest=digest,
        )


def candidate_digest(case: EvaluatorContractCase, *, repo_root: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="nixbench-contract-digest-") as temp:
        starter = Path(temp) / "starter"
        shutil.copytree(repo_root / "tasks" / case.task_id / "starter", starter, symlinks=True)
        apply_contract_candidate(case, starter)
        return tree_digest(starter)


def apply_contract_candidate(case: EvaluatorContractCase, starter: Path) -> None:
    for relative in case.delete:
        target = starter / relative
        _require_within(target, starter)
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
    for operation in case.rename:
        source_path = starter / operation.source
        destination = starter / operation.destination
        _require_within(source_path, starter)
        _require_within(destination, starter)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(destination)
    shutil.copytree(case.candidate_dir, starter, dirs_exist_ok=True, symlinks=True)


def collect_contract_evidence(
    tasks: Sequence[Task],
    cases: Sequence[EvaluatorContractCase],
    *,
    repo_root: Path,
    results_dir: Path,
    run_prefix: str,
    repetitions: int = 2,
) -> dict[str, dict[str, Any]]:
    if repetitions < 2:
        raise ValueError("contract evidence requires at least two repetitions")
    task_by_id = {task.id: task for task in tasks}
    runs_by_task: dict[str, list[ContractRun]] = {task.id: [] for task in tasks}
    digests: dict[tuple[str, str], str] = {}
    for case in cases:
        if case.task_id not in task_by_id:
            continue
        for index in range(repetitions):
            run = run_contract_case(
                case,
                repo_root=repo_root,
                results_dir=results_dir,
                run_id=f"{run_prefix}-{case.task_id}-{case.id}-{index}",
            )
            runs_by_task[case.task_id].append(run)
            digests[(case.task_id, case.id)] = run.candidate_digest

    global_coverage_errors = coverage_errors(
        tasks, cases, candidate_digests=digests
    )
    evidence: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_cases = [case for case in cases if case.task_id == task.id]
        task_runs = runs_by_task[task.id]
        grouped: dict[str, list[ContractRun]] = {}
        for run in task_runs:
            grouped.setdefault(run.case.id, []).append(run)
        deterministic = all(
            len({_contract_signature(run.result) for run in repeated}) == 1
            for repeated in grouped.values()
        )
        result_errors = [
            error for run in task_runs for error in contract_result_errors(run)
        ]
        evaluator_error_count = sum(
            "error:" in run.log.lower() for run in task_runs
        )
        reference_digest = tree_digest(task.root / "reference")
        alternative_pass_digests = {
            digests[(case.task_id, case.id)]
            for case in task_cases
            if case.outcome == "pass"
            and digests[(case.task_id, case.id)] != reference_digest
        }
        evidence[task.id] = {
            "pass_fixture_count": sum(case.outcome == "pass" for case in task_cases),
            "reject_fixture_count": sum(case.outcome == "reject" for case in task_cases),
            "alternative_pass_fixture_count": len(alternative_pass_digests),
            "criterion_coverage": sorted(
                {
                    case.criterion_id
                    for case in task_cases
                    if case.outcome == "reject"
                }
            ),
            "contract_outcomes_match": not result_errors,
            "contract_errors": result_errors,
            "contract_evaluator_error_count": evaluator_error_count,
            "contract_deterministic": deterministic,
            "contract_durations_seconds": [
                run.result.check.duration_seconds for run in task_runs
            ],
            "contract_invalid_measurement_count": sum(
                run.result.measurement_status != "valid" for run in task_runs
            ),
            "known_issue_count": sum(
                case.known_issue is not None for case in task_cases
            ),
            "contract_coverage_errors": [
                error
                for error in global_coverage_errors
                if error.startswith(f"{task.id}:")
            ],
            "candidate_digests": {
                case.id: digests[(case.task_id, case.id)] for case in task_cases
            },
            "observed_criterion_vectors": {
                case_id: dict(repeated[0].result.criteria)
                for case_id, repeated in grouped.items()
            },
        }
    return evidence


def contract_result_errors(run: ContractRun) -> list[str]:
    case = run.case
    result = run.result
    prefix = f"{case.task_id}/{case.id}"
    errors: list[str] = []
    if result.criteria != case.expected_criteria:
        errors.append(
            f"{prefix}: actual criterion vector {result.criteria!r} does not equal expected {case.expected_criteria!r}"
        )
    if case.outcome == "pass":
        if not result.passed or result.measurement_status != "valid":
            errors.append(f"{prefix}: passing fixture did not pass validly")
    else:
        if result.measurement_status != "valid" or result.task_outcome != "fail" or result.passed:
            errors.append(f"{prefix}: rejecting fixture did not reject validly")
        if result.criteria.get(case.criterion_id) is not False:
            errors.append(f"{prefix}: named criterion {case.criterion_id} was not false")
    if result.check.timed_out:
        errors.append(f"{prefix}: evaluator timed out")
    return errors


def coverage_errors(
    tasks: Sequence[Task],
    cases: Sequence[EvaluatorContractCase],
    *,
    candidate_digests: Mapping[tuple[str, str], str] | None = None,
) -> list[str]:
    errors: list[str] = []
    by_task: dict[str, list[EvaluatorContractCase]] = {}
    for case in cases:
        by_task.setdefault(case.task_id, []).append(case)
    for task in sorted(tasks, key=lambda item: item.id):
        task_cases = by_task.get(task.id, [])
        outcomes = {case.outcome for case in task_cases}
        for outcome in sorted(VALID_OUTCOMES - outcomes):
            errors.append(f"{task.id}: missing {outcome} contract case")
        targeted = {
            case.criterion_id for case in task_cases if case.outcome == "reject"
        }
        for criterion in task.criteria:
            if criterion.required and criterion.id not in targeted:
                errors.append(
                    f"{task.id}: missing targeted rejecting fixture for required criterion {criterion.id}"
                )

    if candidate_digests is not None:
        duplicate_groups: dict[tuple[str, str], list[EvaluatorContractCase]] = {}
        for case in cases:
            if case.outcome != "reject":
                continue
            digest = candidate_digests[(case.task_id, case.id)]
            duplicate_groups.setdefault((case.task_id, digest), []).append(case)
        for (task_id, _), duplicates in duplicate_groups.items():
            if len(duplicates) < 2:
                continue
            if all(case.duplicate_candidate_reason for case in duplicates):
                continue
            labels = ", ".join(sorted(case.id for case in duplicates))
            errors.append(
                f"{task_id}: duplicate rejecting candidate digest used by {labels} without duplicate_candidate_reason"
            )
    return errors


def _contract_signature(result: TaskRunResult) -> tuple[object, ...]:
    return (
        result.measurement_status,
        result.task_outcome,
        result.passed,
        result.score,
        result.max_score,
        tuple(sorted(result.criteria.items())),
        tuple(result.failure_classes),
        result.invalid_reason,
        result.check.returncode,
        result.check.timed_out,
    )


def tree_digest(root: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(b"nixbench-contract-candidate-v1\0")
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        metadata = path.lstat()
        hasher.update(len(relative).to_bytes(8, "big"))
        hasher.update(relative)
        if stat.S_ISLNK(metadata.st_mode):
            kind = b"symlink"
            payload = os.readlink(path).encode("utf-8")
        elif stat.S_ISREG(metadata.st_mode):
            kind = b"file+x" if metadata.st_mode & stat.S_IXUSR else b"file"
            payload = path.read_bytes()
        elif stat.S_ISDIR(metadata.st_mode):
            continue
        else:
            raise ValueError(f"unsupported candidate file kind: {path}")
        hasher.update(len(kind).to_bytes(8, "big"))
        hasher.update(kind)
        hasher.update(len(payload).to_bytes(8, "big"))
        hasher.update(payload)
    return hasher.hexdigest()


def _boolean_table(value: object, label: str) -> dict[str, bool]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and type(item) is bool for key, item in value.items()
    ):
        raise ValueError(f"{label} must be a table of criterion booleans")
    return dict(value)


def _string_table(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(item, str) and item.strip()
        for key, item in value.items()
    ):
        raise ValueError(f"{label} must be a table of nonempty strings")
    return dict(value)


def _optional_nonempty_string(value: object, path: Path, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {field} must be nonempty")
    return value


def _safe_relative_path(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"{label} must stay inside the candidate workspace")
    return path


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be a list of strings")
    return value


def _require_within(path: Path, root: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"candidate operation escapes workspace: {path}") from exc
