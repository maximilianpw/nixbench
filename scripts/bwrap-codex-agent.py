#!/usr/bin/env python3
from __future__ import annotations

import argparse
import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nixbench.isolation import (
    APPROVED_HELDOUT_PROFILE,
    APPROVED_PREFLIGHT_EVIDENCE,
    build_bubblewrap_command,
    read_isolation_preflight,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Codex in the approved NixBench bubblewrap profile."
    )
    parser.add_argument("--codex-bin", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--network-policy", choices=("enabled", "disabled"), required=True)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command or "--json" not in command:
        parser.error("the Codex command must include --json")

    status_value = os.environ.get("NIXBENCH_AGENT_STATUS_FILE")
    if not status_value:
        parser.error("NIXBENCH_AGENT_STATUS_FILE is required")
    status_path = Path(status_value)
    if args.prompt_file is not None:
        command.append(args.prompt_file.read_text(encoding="utf-8"))

    codex_bin, readonly_bindings = _resolve_agent_executable(args.codex_bin)

    preflight_command = build_bubblewrap_command(
        workspace=args.workspace,
        forbidden_paths=(),
        command=["/bin/sh", "-c", ":"],
        network_policy=args.network_policy,
        readonly_bindings=readonly_bindings,
        record_preflight=True,
    )
    preflight = subprocess.run(
        preflight_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    evidence = APPROVED_PREFLIGHT_EVIDENCE
    preflight_result = read_isolation_preflight(args.workspace)
    if preflight.returncode != 0 or preflight_result is None:
        _write_status(
            status_path,
            preflight=False,
            evidence=f"{APPROVED_HELDOUT_PROFILE}:preflight-failed",
            completed=False,
            transport_error="isolation-preflight-failed",
            launcher_exit=preflight.returncode,
        )
        if preflight.stderr:
            sys.stderr.write(preflight.stderr)
        return preflight.returncode or 125
    _write_status(
        status_path,
        preflight=True,
        evidence=evidence,
        completed=False,
        transport_error=None,
        launcher_exit=None,
    )

    isolated = build_bubblewrap_command(
        workspace=args.workspace,
        forbidden_paths=(),
        command=[codex_bin, *command],
        network_policy=args.network_policy,
        readonly_bindings=readonly_bindings,
    )
    try:
        process = subprocess.Popen(
            isolated,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        _write_status(
            status_path,
            preflight=True,
            evidence=evidence,
            completed=False,
            transport_error="isolated-launch-error",
            launcher_exit=None,
        )
        return 2

    completed = False
    transport_error: str | None = None
    if process.stdout is None:
        transport_error = "isolated-output-unavailable"
    else:
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
            if event_type == "turn.completed":
                completed = True
            elif event_type in {"error", "turn.failed"}:
                transport_error = transport_error or f"codex-{event_type}-event"
    launcher_exit = process.wait()
    if launcher_exit != 0:
        completed = False
        transport_error = transport_error or f"codex-launcher-exit-{launcher_exit}"
    elif not completed:
        transport_error = transport_error or "codex-turn-incomplete"
    if transport_error is not None:
        completed = False
    _write_status(
        status_path,
        preflight=True,
        evidence=evidence,
        completed=completed,
        transport_error=transport_error,
        launcher_exit=launcher_exit,
    )
    return launcher_exit


def _resolve_agent_executable(value: str) -> tuple[str, dict[Path, str]]:
    if value.startswith("/workspace/"):
        return value, {}
    located = shutil.which(value)
    source = Path(located or value).resolve()
    if not source.is_file():
        raise ValueError(f"agent executable is missing: {value}")
    staging = Path(
        tempfile.mkdtemp(prefix="nixbench-isolated-agent-", dir="/tmp")
    )
    staged_agent = staging / "agent"
    shutil.copy2(source, staged_agent)
    atexit.register(shutil.rmtree, staging, True)
    return "/run/nixbench/agent", {staged_agent: "/run/nixbench/agent"}


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
