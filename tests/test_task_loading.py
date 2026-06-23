from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from nixbench.task import find_task, iter_tasks


class TaskLoadingTests(unittest.TestCase):
    def test_iter_tasks_loads_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_dir = root / "toy"
            (task_dir / "starter").mkdir(parents=True)
            (task_dir / "reference").mkdir()
            (task_dir / "tests").mkdir()
            (task_dir / "prompt.md").write_text("Do the thing.\n")
            (task_dir / "tests" / "check.sh").write_text("exit 0\n")
            (task_dir / "metadata.toml").write_text(
                "\n".join(
                    [
                        'id = "toy-task"',
                        'name = "Toy Task"',
                        'category = "toy"',
                        'difficulty = "easy"',
                        "timeout_seconds = 5",
                        "max_score = 25",
                        'systems = ["any"]',
                        'evaluator = "tests/check.sh"',
                    ]
                )
                + "\n"
            )

            tasks = iter_tasks(root)

            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].id, "toy-task")
            self.assertEqual(tasks[0].max_score, 25)
            found = find_task(root, "toy-task")
            self.assertEqual(found.id, tasks[0].id)
            self.assertEqual(found.root, tasks[0].root)


if __name__ == "__main__":
    unittest.main()
