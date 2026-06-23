from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


class TaskError(RuntimeError):
    """Raised when a benchmark task is malformed."""


@dataclass(frozen=True)
class Task:
    root: Path
    metadata: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.metadata.get("id") or self.root.name)

    @property
    def name(self) -> str:
        return str(self.metadata.get("name") or self.id)

    @property
    def category(self) -> str:
        return str(self.metadata.get("category") or "uncategorized")

    @property
    def difficulty(self) -> str:
        return str(self.metadata.get("difficulty") or "unknown")

    @property
    def timeout_seconds(self) -> int:
        return int(self.metadata.get("timeout_seconds") or 120)

    @property
    def max_score(self) -> float:
        return float(self.metadata.get("max_score") or 100)

    @property
    def systems(self) -> list[str]:
        systems = self.metadata.get("systems") or ["any"]
        if not isinstance(systems, list) or not all(isinstance(item, str) for item in systems):
            raise TaskError(f"{self.id}: systems must be a list of strings")
        return systems

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
        evaluator = self.metadata.get("evaluator") or "tests/check.sh"
        return self.root / str(evaluator)

    def supports_system(self, system: str | None) -> bool:
        if system is None:
            return True
        return "any" in self.systems or system in self.systems

    def validate(self) -> None:
        required = [
            self.prompt_path,
            self.starter_dir,
            self.reference_dir,
            self.tests_dir,
            self.evaluator_path,
        ]
        missing = [path for path in required if not path.exists()]
        if missing:
            missing_list = ", ".join(str(path) for path in missing)
            raise TaskError(f"{self.id}: missing required task files: {missing_list}")


def load_task(path: Path) -> Task:
    metadata_path = path / "metadata.toml"
    if not metadata_path.exists():
        raise TaskError(f"{path}: missing metadata.toml")

    with metadata_path.open("rb") as handle:
        metadata = tomllib.load(handle)

    task = Task(root=path.resolve(), metadata=metadata)
    task.validate()
    return task


def iter_tasks(tasks_dir: Path) -> list[Task]:
    if not tasks_dir.exists():
        raise TaskError(f"tasks directory does not exist: {tasks_dir}")

    tasks: list[Task] = []
    for child in sorted(tasks_dir.iterdir()):
        if child.is_dir() and (child / "metadata.toml").exists():
            tasks.append(load_task(child))
    return tasks


def find_task(tasks_dir: Path, task_id: str) -> Task:
    for task in iter_tasks(tasks_dir):
        if task.id == task_id or task.root.name == task_id:
            return task
    raise TaskError(f"unknown task: {task_id}")
