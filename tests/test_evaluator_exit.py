from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nixbench.evaluator_exit import evaluator_exit_code


class EvaluatorExitTests(unittest.TestCase):
    def test_optional_criterion_does_not_force_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "metadata.toml"
            metadata.write_text(
                """
max_score = 100
[[criteria]]
id = "works"
points = 90
required = true
failure_class = "evaluation"
[[criteria]]
id = "formatting"
points = 10
required = false
failure_class = "formatting"
"""
            )
            score = root / "score.json"
            score.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "criteria": {"works": True, "formatting": False},
                        "notes": [],
                    }
                )
            )

            self.assertEqual(evaluator_exit_code(metadata, score), 0)

    def test_failed_required_criterion_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "metadata.toml"
            metadata.write_text(
                """
max_score = 100
[[criteria]]
id = "works"
points = 100
required = true
failure_class = "evaluation"
"""
            )
            score = root / "score.json"
            score.write_text(
                '{"schema_version":2,"criteria":{"works":false},"notes":[]}'
            )

            self.assertEqual(evaluator_exit_code(metadata, score), 1)


if __name__ == "__main__":
    unittest.main()
