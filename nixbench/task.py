from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


class TaskError(RuntimeError):
    """Raised when a benchmark task is malformed."""


REQUIRED_METADATA_FIELDS = {
    "id",
    "name",
    "category",
    "difficulty",
    "timeout_seconds",
    "max_score",
    "systems",
    "evaluator",
}
TASK_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


@dataclass(frozen=True)
class Task:
    root: Path
    metadata: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.metadata["id"])

    @property
    def name(self) -> str:
        return str(self.metadata["name"])

    @property
    def category(self) -> str:
        return str(self.metadata["category"])

    @property
    def difficulty(self) -> str:
        return str(self.metadata["difficulty"])

    @property
    def timeout_seconds(self) -> int:
        return int(self.metadata["timeout_seconds"])

    @property
    def max_score(self) -> float:
        return float(self.metadata["max_score"])

    @property
    def systems(self) -> list[str]:
        return list(self.metadata["systems"])

    @property
    def prompt_path(self) -> Path:
        return self.root / "prompt.md"

    @property
    def starter_dir(self) -> Path:
        return self.root / "starter"

    @property
    def reference_dir(self) -> Path:
        return self.root / "reference"

    @property
    def tests_dir(self) -> Path:
        return self.root / "tests"

    @property
    def evaluator_path(self) -> Path:
        return self.root / str(self.metadata["evaluator"])

    def supports_system(self, system: str | None) -> bool:
        if system is None:
            return True
        return "any" in self.systems or system in self.systems

    def validate(self) -> None:
        missing_fields = sorted(REQUIRED_METADATA_FIELDS - self.metadata.keys())
        if missing_fields:
            raise TaskError(f"{self.root}: missing required metadata fields: {', '.join(missing_fields)}")

        task_id = self.metadata["id"]
        if not isinstance(task_id, str) or TASK_ID_PATTERN.fullmatch(task_id) is None:
            raise TaskError(f"{self.root}: id must be a lowercase hyphenated slug")

        for field in ("name", "category"):
            value = self.metadata[field]
            if not isinstance(value, str) or not value.strip():
                raise TaskError(f"{task_id}: {field} must be a non-empty string")

        difficulty = self.metadata["difficulty"]
        if not isinstance(difficulty, str) or difficulty not in VALID_DIFFICULTIES:
            choices = ", ".join(sorted(VALID_DIFFICULTIES))
            raise TaskError(f"{task_id}: difficulty must be one of: {choices}")

        timeout_seconds = self.metadata["timeout_seconds"]
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise TaskError(f"{task_id}: timeout_seconds must be a positive integer")

        max_score = self.metadata["max_score"]
        if not _is_positive_finite_number(max_score):
            raise TaskError(f"{task_id}: max_score must be a positive finite number")

        systems = self.metadata["systems"]
        if (
            not isinstance(systems, list)
            or not systems
            or not all(isinstance(item, str) and item.strip() for item in systems)
        ):
            raise TaskError(f"{task_id}: systems must be a non-empty list of strings")
        if len(set(systems)) != len(systems):
            raise TaskError(f"{task_id}: systems must not contain duplicates")

        evaluator = self.metadata["evaluator"]
        if not isinstance(evaluator, str) or not evaluator.strip():
            raise TaskError(f"{task_id}: evaluator must be a non-empty relative path")
        evaluator_rel = Path(evaluator)
        if evaluator_rel.is_absolute():
            raise TaskError(f"{task_id}: evaluator must stay within the task directory")
        evaluator_path = (self.root / evaluator_rel).resolve()
        if not _path_is_within(evaluator_path, self.root):
            raise TaskError(f"{task_id}: evaluator must stay within the task directory")

        required_files = [self.prompt_path, evaluator_path]
        invalid_files = [
            path for path in required_files if not path.is_file() or not _path_is_within(path, self.root)
        ]
        required_dirs = [self.starter_dir, self.reference_dir, self.tests_dir]
        invalid_dirs = [
            path for path in required_dirs if not path.is_dir() or not _path_is_within(path, self.root)
        ]
        invalid_paths = invalid_files + invalid_dirs
        if invalid_paths:
            path_list = ", ".join(str(path) for path in invalid_paths)
            raise TaskError(f"{task_id}: missing or invalid required task paths: {path_list}")


def load_task(path: Path) -> Task:
    metadata_path = path / "metadata.toml"
    if not metadata_path.is_file():
        raise TaskError(f"{path}: missing or invalid metadata.toml")

    with metadata_path.open("rb") as handle:
        metadata = tomllib.load(handle)

    task = Task(root=path.resolve(), metadata=metadata)
    task.validate()
    return task


def iter_tasks(tasks_dir: Path) -> list[Task]:
    if not tasks_dir.is_dir():
        raise TaskError(f"tasks directory does not exist or is not a directory: {tasks_dir}")

    tasks: list[Task] = []
    task_roots_by_id: dict[str, Path] = {}
    for child in sorted(tasks_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "metadata.toml").is_file():
            raise TaskError(f"{child}: task directory is missing metadata.toml")
        task = load_task(child)
        previous_root = task_roots_by_id.get(task.id)
        if previous_root is not None:
            raise TaskError(f"duplicate task id {task.id!r}: {previous_root} and {task.root}")
        task_roots_by_id[task.id] = task.root
        tasks.append(task)
    return tasks


def find_task(tasks_dir: Path, task_id: str) -> Task:
    for task in iter_tasks(tasks_dir):
        if task.id == task_id or task.root.name == task_id:
            return task
    raise TaskError(f"unknown task: {task_id}")


def _path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _is_positive_finite_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False
