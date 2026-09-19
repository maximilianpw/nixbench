from __future__ import annotations

import json
import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MAX_AGENT_STATUS_BYTES = 65_536


@dataclass(frozen=True)
class AgentCompletionStatus:
    schema_version: int
    preflight_successful: bool
    preflight_evidence: str
    completed: bool
    transport_error: str | None
    launcher_exit: int | None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def read_agent_status(
    path: Path,
) -> tuple[AgentCompletionStatus | None, str | None]:
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        status_stat = os.fstat(descriptor)
    except FileNotFoundError:
        return None, "missing-agent-attestation"
    except OSError:
        return None, "invalid-agent-attestation"
    if not stat.S_ISREG(status_stat.st_mode) or status_stat.st_size > MAX_AGENT_STATUS_BYTES:
        os.close(descriptor)
        return None, "invalid-agent-attestation"
    try:
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = None
            payload = json.loads(handle.read().decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError):
        return None, "invalid-agent-attestation"
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        return _parse_agent_status(payload), None
    except ValueError:
        return None, "invalid-agent-attestation"


def _parse_agent_status(payload: object) -> AgentCompletionStatus:
    if not isinstance(payload, dict):
        raise ValueError("status must be an object")
    expected = {
        "schema_version",
        "preflight",
        "completed",
        "transport_error",
        "launcher_exit",
    }
    if set(payload) != expected or payload["schema_version"] != 1:
        raise ValueError("status fields do not match schema 1")
    preflight = payload["preflight"]
    if not isinstance(preflight, dict) or set(preflight) != {"successful", "evidence"}:
        raise ValueError("invalid preflight")
    if type(preflight["successful"]) is not bool:
        raise ValueError("invalid preflight outcome")
    evidence = preflight["evidence"]
    if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 1_000:
        raise ValueError("invalid preflight evidence")
    if type(payload["completed"]) is not bool:
        raise ValueError("invalid completion outcome")
    transport_error = payload["transport_error"]
    if transport_error is not None and (
        not isinstance(transport_error, str)
        or not transport_error.strip()
        or len(transport_error) > 1_000
    ):
        raise ValueError("invalid transport error")
    launcher_exit = payload["launcher_exit"]
    if launcher_exit is not None and (
        type(launcher_exit) is not int or launcher_exit < 0
    ):
        raise ValueError("invalid launcher exit")
    if payload["completed"] and transport_error is not None:
        raise ValueError("completed status cannot contain a transport error")
    return AgentCompletionStatus(
        schema_version=1,
        preflight_successful=preflight["successful"],
        preflight_evidence=evidence,
        completed=payload["completed"],
        transport_error=transport_error,
        launcher_exit=launcher_exit,
    )
