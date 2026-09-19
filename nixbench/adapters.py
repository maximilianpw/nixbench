from __future__ import annotations

import hashlib
import shlex
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence


ADAPTER_BUNDLE_DIGEST_DOMAIN = b"nixbench-trusted-adapter-bundle-v1"


class _Digest(Protocol):
    def update(self, value: bytes) -> None: ...


def adapter_bundle_sha256(repository_root: Path, files: Sequence[Path]) -> str:
    """Hash an adapter's declared local trust boundary canonically."""
    root = repository_root.resolve()
    members: list[tuple[str, Path]] = []
    for file_path in files:
        if file_path.is_symlink():
            raise ValueError(f"trusted adapter bundle member must not be a symlink: {file_path}")
        resolved = file_path.resolve()
        try:
            relative = resolved.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError(
                f"trusted adapter bundle member is outside the repository: {file_path}"
            ) from exc
        if not resolved.is_file():
            raise ValueError(f"trusted adapter bundle member is missing: {file_path}")
        members.append((relative, resolved))

    members.sort(key=lambda member: member[0])
    names = [name for name, _ in members]
    if len(names) != len(set(names)):
        raise ValueError("trusted adapter bundle contains duplicate members")
    if not members:
        raise ValueError("trusted adapter bundle must contain at least one file")

    digest = hashlib.sha256()
    _hash_length_prefixed(digest, ADAPTER_BUNDLE_DIGEST_DOMAIN)
    _hash_length_prefixed(digest, len(members).to_bytes(8, "big"))
    for relative, resolved in members:
        mode = resolved.stat().st_mode
        _hash_length_prefixed(digest, relative.encode("utf-8"))
        _hash_length_prefixed(
            digest,
            b"\x01" if mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH) else b"\x00",
        )
        _hash_length_prefixed(digest, resolved.read_bytes())
    return digest.hexdigest()


def _hash_length_prefixed(digest: _Digest, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


@dataclass(frozen=True)
class TrustedAdapter:
    id: str
    executable: Path
    trust: str
    repository_root: Path
    bundle_files: tuple[Path, ...]
    isolation_profile: str | None = None

    @property
    def sha256(self) -> str:
        """Legacy entry-point digest retained without changing its meaning."""
        return hashlib.sha256(self.executable.read_bytes()).hexdigest()

    @property
    def bundle_sha256(self) -> str:
        return adapter_bundle_sha256(self.repository_root, self.bundle_files)

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
_CODEX_ADAPTER = _REPOSITORY_ROOT / "scripts" / "codex-agent-adapter.py"
_BWRAP_ADAPTER = _REPOSITORY_ROOT / "scripts" / "bwrap-codex-agent.py"
TRUSTED_ADAPTERS = {
    "codex-json": TrustedAdapter(
        id="codex-json",
        executable=_CODEX_ADAPTER,
        trust="provisional-same-uid",
        repository_root=_REPOSITORY_ROOT,
        bundle_files=(_CODEX_ADAPTER,),
    ),
    "codex-json-bwrap": TrustedAdapter(
        id="codex-json-bwrap",
        executable=_BWRAP_ADAPTER,
        trust="approved-linux-bwrap-v1",
        repository_root=_REPOSITORY_ROOT,
        bundle_files=(
            _BWRAP_ADAPTER,
            _REPOSITORY_ROOT / "nixbench" / "isolation.py",
            _REPOSITORY_ROOT / "launchers" / "linux-bwrap-v1.toml",
        ),
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
