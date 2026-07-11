from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nixbench.task import REQUIRED_METADATA_FIELDS, TaskError, find_task, iter_tasks, load_task


class TaskLoadingTests(unittest.TestCase):
    def test_iter_tasks_loads_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_task(root, directory="toy", overrides={"id": "toy-task", "max_score": 25})

            tasks = iter_tasks(root)

            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].id, "toy-task")
            self.assertEqual(tasks[0].max_score, 25)
            found = find_task(root, "toy-task")
            self.assertEqual(found.id, tasks[0].id)
            self.assertEqual(found.root, tasks[0].root)

    def test_all_documented_metadata_fields_are_required(self) -> None:
        for field in sorted(REQUIRED_METADATA_FIELDS):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                task_dir = make_task(root, omitted={field})

                with self.assertRaisesRegex(TaskError, field):
                    load_task(task_dir)

    def test_invalid_metadata_values_are_rejected(self) -> None:
        cases = {
            "id-path": {"id": "../escape"},
            "id-uppercase": {"id": "Toy"},
            "empty-name": {"name": ""},
            "empty-category": {"category": ""},
            "unknown-difficulty": {"difficulty": "expert"},
            "zero-timeout": {"timeout_seconds": 0},
            "fractional-timeout": {"timeout_seconds": 1.5},
            "boolean-timeout": {"timeout_seconds": True},
            "zero-max-score": {"max_score": 0},
            "non-finite-max-score": {"max_score": float("nan")},
            "overflowing-max-score": {"max_score": int("9" * 400)},
            "boolean-max-score": {"max_score": True},
            "empty-systems": {"systems": []},
            "string-systems": {"systems": "any"},
            "duplicate-systems": {"systems": ["any", "any"]},
            "empty-system": {"systems": [""]},
            "empty-evaluator": {"evaluator": ""},
            "absolute-evaluator": {"evaluator": "/tmp/check.sh"},
            "escaping-evaluator": {"evaluator": "../check.sh"},
        }

        for label, overrides in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp:
                task_dir = make_task(Path(temp), overrides=overrides)

                with self.assertRaises(TaskError):
                    load_task(task_dir)

    def test_required_paths_must_have_the_expected_types(self) -> None:
        cases = ("prompt.md", "starter", "reference", "tests", "tests/check.sh")
        for relative_path in cases:
            with self.subTest(path=relative_path), tempfile.TemporaryDirectory() as temp:
                task_dir = make_task(Path(temp))
                path = task_dir / relative_path
                if path.is_dir():
                    for child in path.iterdir():
                        child.unlink()
                    path.rmdir()
                    path.write_text("not a directory\n")
                else:
                    path.unlink()
                    path.mkdir()

                with self.assertRaises(TaskError):
                    load_task(task_dir)

    def test_iter_tasks_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_task(root, directory="first", overrides={"id": "duplicate"})
            make_task(root, directory="second", overrides={"id": "duplicate"})

            with self.assertRaisesRegex(TaskError, "duplicate task id"):
                iter_tasks(root)

    def test_required_paths_cannot_escape_through_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_dir = make_task(root / "tasks")
            external = root / "external"
            external.mkdir()
            starter = task_dir / "starter"
            starter.rmdir()
            starter.symlink_to(external, target_is_directory=True)

            with self.assertRaises(TaskError):
                load_task(task_dir)

    def test_iter_tasks_rejects_incomplete_task_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "incomplete-task").mkdir()

            with self.assertRaisesRegex(TaskError, "missing metadata.toml"):
                iter_tasks(root)


def make_task(
    root: Path,
    *,
    directory: str = "toy",
    overrides: dict[str, object] | None = None,
    omitted: set[str] | None = None,
) -> Path:
    task_dir = root / directory
    (task_dir / "starter").mkdir(parents=True)
    (task_dir / "reference").mkdir()
    (task_dir / "tests").mkdir()
    (task_dir / "prompt.md").write_text("Do the thing.\n")
    (task_dir / "tests" / "check.sh").write_text("exit 0\n")

    metadata: dict[str, object] = {
        "id": "toy",
        "name": "Toy Task",
        "category": "toy",
        "difficulty": "easy",
        "timeout_seconds": 5,
        "max_score": 100,
        "systems": ["any"],
        "evaluator": "tests/check.sh",
    }
    if overrides:
        metadata.update(overrides)
    for field in omitted or set():
        metadata.pop(field, None)

    lines = [f"{key} = {toml_value(value)}" for key, value in metadata.items()]
    (task_dir / "metadata.toml").write_text("\n".join(lines) + "\n")
    return task_dir


def toml_value(value: object) -> str:
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return str(value)


if __name__ == "__main__":
    unittest.main()
