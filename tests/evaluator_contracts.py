from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]

from nixbench.runner import TaskRunResult, run_task
from nixbench.task import TASK_ID_PATTERN, load_task


VALID_OUTCOMES = {"pass", "reject"}


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
    root: Path
    candidate_dir: Path
    delete: tuple[PurePosixPath, ...]
    rename: tuple[RenameOperation, ...]
    known_issue: str | None


def load_contract_cases(
    contracts_root: Path, *, tasks_root: Path | None = None
) -> tuple[EvaluatorContractCase, ...]:
    contracts_root = contracts_root.resolve()
    if not contracts_root.is_dir():
        raise ValueError(f"contracts root does not exist: {contracts_root}")
    known_tasks = None
    task_criteria: dict[str, set[str]] = {}
    if tasks_root is not None:
        known_tasks = {path.name for path in tasks_root.iterdir() if path.is_dir()}
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
        if known_tasks is not None and task_dir_id not in known_tasks:
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
        }
        optional = {"delete", "rename", "known_issue"}
        missing = sorted(required - data.keys())
        unknown = sorted(data.keys() - required - optional)
        if missing:
            raise ValueError(f"{manifest_path}: missing fields: {', '.join(missing)}")
        if unknown:
            raise ValueError(f"{manifest_path}: unknown fields: {', '.join(unknown)}")
        if type(data["schema_version"]) is not int or data["schema_version"] != 2:
            raise ValueError(f"{manifest_path}: schema_version must be 2")
        if data["task_id"] != task_dir_id:
            raise ValueError(f"{manifest_path}: task_id does not match its directory")
        outcome = data["outcome"]
        if outcome not in VALID_OUTCOMES:
            raise ValueError(f"{manifest_path}: outcome must be pass or reject")
        for field in ("criterion_id", "description"):
            if not isinstance(data[field], str) or not data[field].strip():
                raise ValueError(f"{manifest_path}: {field} must be nonempty")
        if task_dir_id in task_criteria and data["criterion_id"] not in task_criteria[task_dir_id]:
            raise ValueError(
                f"{manifest_path}: criterion_id is not declared by task {task_dir_id}"
            )
        known_issue = data.get("known_issue")
        if known_issue is not None and (
            not isinstance(known_issue, str) or not known_issue.strip()
        ):
            raise ValueError(f"{manifest_path}: known_issue must be nonempty")
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
                criterion_id=data["criterion_id"],
                description=data["description"],
                root=case_root,
                candidate_dir=candidate_dir,
                delete=delete,
                rename=tuple(rename),
                known_issue=known_issue,
            )
        )
    return tuple(cases)


def run_contract_case(
    case: EvaluatorContractCase, *, repo_root: Path
) -> tuple[TaskRunResult, str]:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = repo_root / "tasks" / case.task_id
        task_root = root / "tasks" / case.task_id
        shutil.copytree(source, task_root, symlinks=True)
        starter = task_root / "starter"
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
        task = load_task(task_root)
        result = run_task(
            task,
            results_dir=root / "results",
            run_id=f"{case.task_id}-{case.id}",
            solution_mode="starter",
        )
        return result, Path(result.check.log_path).read_text()


def coverage_errors(
    task_ids: set[str],
    cases: tuple[EvaluatorContractCase, ...],
    *,
    required_criteria: dict[str, set[str]] | None = None,
) -> list[str]:
    errors: list[str] = []
    by_task: dict[str, set[str]] = {}
    for case in cases:
        by_task.setdefault(case.task_id, set()).add(case.outcome)
    for task_id in sorted(task_ids):
        outcomes = by_task.get(task_id, set())
        for outcome in sorted(VALID_OUTCOMES - outcomes):
            errors.append(f"{task_id}: missing {outcome} contract case")
        if required_criteria is not None:
            covered = {
                case.criterion_id for case in cases if case.task_id == task_id
            }
            for criterion_id in sorted(required_criteria[task_id] - covered):
                errors.append(
                    f"{task_id}: missing fixture for required criterion {criterion_id}"
                )
    return errors


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
