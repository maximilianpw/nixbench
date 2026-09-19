#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run codex JSONL mode and write trusted NixBench completion status."
    )
    parser.add_argument("--codex-bin", default="codex")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or "--json" not in command:
        parser.error("the Codex command must include --json")
    if args.prompt_file is not None:
        command.append(args.prompt_file.read_text(encoding="utf-8"))

    status_value = os.environ.get("NIXBENCH_AGENT_STATUS_FILE")
    if not status_value:
        parser.error("NIXBENCH_AGENT_STATUS_FILE is required")
    status_path = Path(status_value)
    child_env = os.environ.copy()
    for private_name in (
        "NIXBENCH_AGENT_STATUS_FILE",
        "NIXBENCH_SCORE_FILE",
        "NIXBENCH_TASK_DIR",
        "NIXBENCH_EVALUATOR_EXIT",
    ):
        child_env.pop(private_name, None)

    preflight = False
    completed = False
    transport_error: str | None = None
    try:
        process = subprocess.Popen(
            [args.codex_bin, *command],
            env=child_env,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        _write_status(
            status_path,
            preflight=False,
            evidence="codex-launch-failed",
            completed=False,
            transport_error="codex-launch-error",
            launcher_exit=None,
        )
        return 2

    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            transport_error = transport_error or "codex-invalid-json-event"
            continue
        if not isinstance(event, dict):
            transport_error = transport_error or "codex-invalid-json-event"
            continue
        event_type = event.get("type")
        if event_type == "thread.started":
            preflight = True
            _write_status(
                status_path,
                preflight=True,
                evidence="codex-thread.started",
                completed=False,
                transport_error=None,
                launcher_exit=None,
            )
        elif event_type == "turn.completed":
            completed = True
        elif event_type in {"error", "turn.failed"}:
            transport_error = transport_error or f"codex-{event_type}-event"

    launcher_exit = process.wait()
    if not completed and transport_error is None:
        transport_error = (
            f"codex-launcher-exit-{launcher_exit}"
            if launcher_exit != 0
            else "codex-turn-incomplete"
        )
    if launcher_exit != 0:
        completed = False
    if transport_error is not None:
        completed = False
    _write_status(
        status_path,
        preflight=preflight,
        evidence="codex-thread.started" if preflight else "codex-thread-not-started",
        completed=completed,
        transport_error=transport_error,
        launcher_exit=launcher_exit,
    )
    return launcher_exit


def _write_status(
    path: Path,
    *,
    preflight: bool,
    evidence: str,
    completed: bool,
    transport_error: str | None,
    launcher_exit: int | None,
) -> None:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "preflight": {"successful": preflight, "evidence": evidence},
        "completed": completed,
        "transport_error": transport_error,
        "launcher_exit": launcher_exit,
    }
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
