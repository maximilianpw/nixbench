from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nixbench.adapters import adapter_bundle_sha256, get_trusted_adapter


REPO_ROOT = Path(__file__).resolve().parents[1]
ADAPTER = REPO_ROOT / "scripts" / "codex-agent-adapter.py"


class CodexAgentAdapterTests(unittest.TestCase):
    def test_bwrap_bundle_digest_covers_declared_security_boundary_only(self) -> None:
        adapter = get_trusted_adapter("codex-json-bwrap")
        expected_members = {
            "scripts/bwrap-codex-agent.py",
            "nixbench/isolation.py",
            "launchers/linux-bwrap-v1.toml",
        }
        self.assertEqual(
            {
                path.resolve().relative_to(adapter.repository_root.resolve()).as_posix()
                for path in adapter.bundle_files
            },
            expected_members,
        )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            copied_members = []
            for source in adapter.bundle_files:
                relative = source.resolve().relative_to(adapter.repository_root.resolve())
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_members.append(destination)
            baseline = adapter_bundle_sha256(root, copied_members)
            self.assertEqual(baseline, adapter_bundle_sha256(root, reversed(copied_members)))

            unrelated = root / "README.md"
            unrelated.write_text("not part of the bundle\n")
            self.assertEqual(baseline, adapter_bundle_sha256(root, copied_members))

            for member in copied_members:
                with self.subTest(member=member.relative_to(root)):
                    original = member.read_bytes()
                    member.write_bytes(original + b"\n# bundle mutation\n")
                    self.assertNotEqual(
                        baseline, adapter_bundle_sha256(root, copied_members)
                    )
                    member.write_bytes(original)

            executable = root / "scripts" / "bwrap-codex-agent.py"
            executable.chmod(0o644)
            self.assertNotEqual(baseline, adapter_bundle_sha256(root, copied_members))

    def test_non_isolated_adapter_has_deterministic_bundle_identity(self) -> None:
        adapter = get_trusted_adapter("codex-json")

        self.assertEqual(adapter.bundle_sha256, adapter.bundle_sha256)
        self.assertRegex(adapter.bundle_sha256, r"^[0-9a-f]{64}$")

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
