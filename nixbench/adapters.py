from __future__ import annotations

import hashlib
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class TrustedAdapter:
    id: str
    executable: Path
    trust: str
    isolation_profile: str | None = None

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.executable.read_bytes()).hexdigest()

    def command(
        self,
        agent_command: str,
        *,
        wrapper_prompt_path: Path | None = None,
        workspace: Path | None = None,
        forbidden_paths: Sequence[Path] = (),
        network_policy: str | None = None,
    ) -> list[str]:
        command = shlex.split(agent_command)
        if not command:
            raise ValueError("agent command must not be empty")
        adapter_command = [
            sys.executable,
            str(self.executable),
            "--codex-bin",
            command[0],
        ]
        if self.isolation_profile is not None:
            if workspace is None:
                raise ValueError("isolated adapter requires a workspace")
            if network_policy not in {"enabled", "disabled"}:
                raise ValueError("isolated adapter requires a resolved network policy")
            adapter_command.extend(
                [
                    "--workspace",
                    str(workspace.resolve()),
                    "--network-policy",
                    network_policy,
                ]
            )
        if wrapper_prompt_path is not None:
            adapter_command.extend(["--prompt-file", str(wrapper_prompt_path.resolve())])
        return [*adapter_command, "--", *command[1:]]


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TRUSTED_ADAPTERS = {
    "codex-json": TrustedAdapter(
        id="codex-json",
        executable=_REPOSITORY_ROOT / "scripts" / "codex-agent-adapter.py",
        trust="provisional-same-uid",
    ),
    "codex-json-bwrap": TrustedAdapter(
        id="codex-json-bwrap",
        executable=_REPOSITORY_ROOT / "scripts" / "bwrap-codex-agent.py",
        trust="approved-linux-bwrap-v1",
        isolation_profile="linux-bwrap-v1",
    ),
}


def get_trusted_adapter(adapter_id: str) -> TrustedAdapter:
    try:
        adapter = TRUSTED_ADAPTERS[adapter_id]
    except KeyError as exc:
        choices = ", ".join(sorted(TRUSTED_ADAPTERS))
        raise ValueError(
            f"unknown trusted agent adapter {adapter_id!r}; choose one of: {choices}"
        ) from exc
    if not adapter.executable.is_file():
        raise ValueError(f"trusted agent adapter executable is missing: {adapter.executable}")
    return adapter
