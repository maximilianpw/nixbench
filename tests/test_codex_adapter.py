from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = REPO_ROOT / "scripts" / "codex-agent-adapter.py"


class CodexAgentAdapterTests(unittest.TestCase):
    def test_completed_turn_writes_native_event_attestation(self) -> None:
        result, status = self.run_adapter(
            [
                {"type": "thread.started", "thread_id": "thread-1"},
                {"type": "turn.started"},
                {"type": "turn.completed", "usage": {"input_tokens": 1}},
            ]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(status["preflight"]["successful"])
        self.assertEqual(status["preflight"]["evidence"], "codex-thread.started")
        self.assertTrue(status["completed"])
        self.assertIsNone(status["transport_error"])
        self.assertEqual(status["launcher_exit"], 0)

    def test_native_error_event_is_a_transport_failure(self) -> None:
        result, status = self.run_adapter(
            [
                {"type": "thread.started", "thread_id": "thread-1"},
                {"type": "error", "message": "connection reset"},
            ]
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(status["completed"])
        self.assertEqual(status["transport_error"], "codex-error-event")
        self.assertEqual(status["launcher_exit"], 0)

    def test_status_path_is_not_exposed_to_codex_child(self) -> None:
        result, status = self.run_adapter(
            [{"type": "thread.started", "thread_id": "thread-1"}],
            report_status_environment=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(status["transport_error"], "codex-turn-incomplete")
        child_event = json.loads(result.stdout.splitlines()[0])
        self.assertEqual(child_event["private_paths_visible"], [])

    def run_adapter(
        self,
        events: list[dict[str, object]],
        *,
        report_status_environment: bool = False,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake = root / "fake-codex.py"
            fake.write_text(
                """#!/usr/bin/env python3
import json
import os
import sys
events = json.loads(os.environ["FAKE_CODEX_EVENTS"])
if os.environ.get("REPORT_STATUS_ENV") == "1":
    private = [name for name in ("NIXBENCH_AGENT_STATUS_FILE", "NIXBENCH_SCORE_FILE", "NIXBENCH_TASK_DIR", "NIXBENCH_EVALUATOR_EXIT") if name in os.environ]
    print(json.dumps({"private_paths_visible": private}))
for event in events:
    print(json.dumps(event), flush=True)
raise SystemExit(int(os.environ.get("FAKE_CODEX_EXIT", "0")))
"""
            )
            fake.chmod(0o755)
            status_path = root / "status.json"
            environment = os.environ.copy()
            environment.update(
                {
                    "NIXBENCH_AGENT_STATUS_FILE": str(status_path),
                    "FAKE_CODEX_EVENTS": json.dumps(events),
                    "REPORT_STATUS_ENV": "1" if report_status_environment else "0",
                    "NIXBENCH_SCORE_FILE": str(root / "score.json"),
                    "NIXBENCH_TASK_DIR": str(root / "hidden-task"),
                    "NIXBENCH_EVALUATOR_EXIT": str(root / "hidden-helper.py"),
                }
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER),
                    "--codex-bin",
                    str(fake),
                    "--",
                    "exec",
                    "--json",
                    "test prompt",
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            return result, json.loads(status_path.read_text())


if __name__ == "__main__":
    unittest.main()
