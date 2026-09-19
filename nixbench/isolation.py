from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Sequence


APPROVED_HELDOUT_PROFILE = "linux-bwrap-v1"
APPROVED_PREFLIGHT_EVIDENCE = (
    "linux-bwrap-v1:generic-surfaces-absent,neutral-mounts,"
    "workspace-writable,nix-daemon-absent"
)
NIX_DAEMON_SOCKET = Path("/nix/var/nix/daemon-socket/socket")
PREFLIGHT_RECORD = ".nixbench-isolation-preflight"


def build_bubblewrap_command(
    *,
    workspace: Path,
    forbidden_paths: Sequence[Path],
    command: Sequence[str],
    network_policy: str,
    readonly_bindings: Mapping[Path, str] | None = None,
    record_preflight: bool = False,
) -> list[str]:
    del forbidden_paths
    if not command:
        raise ValueError("isolated command must not be empty")
    if network_policy not in {"enabled", "disabled"}:
        raise ValueError("held-out isolation requires an enabled or disabled network policy")
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError(f"isolation workspace is not a directory: {workspace}")
    bwrap = shutil.which("bwrap")
    if bwrap is None:
        raise ValueError("linux-bwrap-v1 requires bubblewrap")

    arguments = [
        bwrap,
        "--die-with-parent",
        "--new-session",
        "--unshare-user",
        "--unshare-pid",
        "--as-pid-1",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup",
    ]
    if network_policy == "disabled":
        arguments.append("--unshare-net")
    arguments.extend(
        [
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--tmpfs",
            "/home",
            "--dir",
            "/home/agent",
            "--bind",
            str(workspace),
            "/workspace",
        ]
    )
    bindings = readonly_bindings or {}
    if bindings:
        arguments.extend(["--dir", "/run", "--dir", "/run/nixbench"])
        for source, target in bindings.items():
            resolved_source = source.resolve()
            if not resolved_source.is_file():
                raise ValueError(f"required isolated executable is missing: {source}")
            if not target.startswith("/run/nixbench/"):
                raise ValueError("extra isolated bindings must use /run/nixbench")
            arguments.extend(["--ro-bind", str(resolved_source), target])
    for system_path in ("/nix/store", "/usr", "/bin", "/lib", "/lib64"):
        if Path(system_path).exists():
            arguments.extend(["--ro-bind", system_path, system_path])
    if network_policy == "enabled":
        for network_path in ("/etc/resolv.conf", "/etc/ssl/certs"):
            if Path(network_path).exists():
                arguments.extend(["--ro-bind", network_path, network_path])

    preflight = _preflight_script(record_preflight=record_preflight)
    inner = [
        "/bin/sh",
        "-c",
        f"( {preflight} ) || exit 125; exec \"$@\"",
        "nixbench-isolation",
        *command,
    ]
    arguments.extend(
        [
            "--clearenv",
            "--setenv",
            "HOME",
            "/home/agent",
            "--setenv",
            "TMPDIR",
            "/tmp",
            "--setenv",
            "PATH",
            "/run/nixbench:/usr/bin:/bin",
            "--setenv",
            "NIXBENCH_WORKDIR",
            "/workspace",
            "--setenv",
            "NIXBENCH_PROMPT",
            "/workspace/NIXBENCH_PROMPT.md",
            "--chdir",
            "/workspace",
            "--",
            *inner,
        ]
    )
    return arguments


def run_isolation_probe(
    *,
    workspace: Path,
    forbidden_paths: Sequence[Path],
    command: Sequence[str],
    network_policy: str,
) -> dict[str, object]:
    bubblewrap_command = build_bubblewrap_command(
        workspace=workspace,
        forbidden_paths=forbidden_paths,
        command=command,
        network_policy=network_policy,
        record_preflight=True,
    )
    completed = subprocess.run(
        bubblewrap_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    preflight = read_isolation_preflight(workspace)
    successful = completed.returncode == 0 and preflight is not None
    return {
        "profile": APPROVED_HELDOUT_PROFILE,
        "successful": successful,
        "forbidden_paths_absent": bool(
            preflight
            and preflight.get("generic_forbidden_surfaces_absent") is True
            and preflight.get("neutral_mounts") is True
        ),
        "generic_forbidden_surfaces_absent": bool(
            preflight
            and preflight.get("generic_forbidden_surfaces_absent") is True
        ),
        "neutral_mounts": bool(
            preflight and preflight.get("neutral_mounts") is True
        ),
        "workspace_writable": bool(
            preflight and preflight.get("workspace_writable") is True
        ),
        "nix_daemon_absent": bool(
            preflight and preflight.get("nix_daemon_absent") is True
        ),
        "returncode": completed.returncode,
        "stderr": completed.stderr[-2_000:],
        "evidence": APPROVED_PREFLIGHT_EVIDENCE if successful else None,
    }


def read_isolation_preflight(workspace: Path) -> dict[str, bool] | None:
    record = workspace / PREFLIGHT_RECORD
    try:
        if record.is_symlink() or not record.is_file() or record.stat().st_size > 1_024:
            return None
        values = {}
        for line in record.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if not separator or value not in {"true", "false"}:
                return None
            values[key] = value == "true"
    except (OSError, UnicodeDecodeError):
        return None
    finally:
        record.unlink(missing_ok=True)
    expected = {
        "generic_forbidden_surfaces_absent",
        "neutral_mounts",
        "workspace_writable",
        "nix_daemon_absent",
    }
    return values if set(values) == expected and all(values.values()) else None


def _preflight_script(*, record_preflight: bool) -> str:
    checks = (
        "workspace_mount=false; home_mount=false; tmp_mount=false; "
        "unexpected_mount=false; "
        "while IFS=' ' read -r mount_id parent_id device mount_root mountpoint "
        "options remainder; do "
        "case \"$mountpoint\" in "
        '  /workspace) case "$mount_root" in /tmp/nixbench-isolated-*/work) ;; '
        "*) unexpected_mount=true ;; esac; "
        'case ",$options," in *,rw,*) workspace_mount=true ;; esac ;; '
        '  /home) case " $remainder " in *" - tmpfs "*) home_mount=true ;; esac ;; '
        '  /tmp) case " $remainder " in *" - tmpfs "*) tmp_mount=true ;; esac ;; '
        '  /run/nixbench/agent) case "$mount_root" in '
        "/tmp/nixbench-isolated-agent-*/agent) "
        'case ",$options," in *,ro,*) ;; *) unexpected_mount=true ;; esac ;; '
        "*) unexpected_mount=true ;; esac ;; "
        "  /repo|/corpus|/reference|/evaluator|/results|/workspace/*|/home/agent/*) "
        "unexpected_mount=true ;; "
        "esac; done < /proc/self/mountinfo; "
        'test "$workspace_mount" = true && test "$home_mount" = true && '
        'test "$tmp_mount" = true && test "$unexpected_mount" = false && '
        'test "$PWD" = /workspace && test "$HOME" = /home/agent && '
        'test "$TMPDIR" = /tmp && test "$NIXBENCH_WORKDIR" = /workspace && '
        f"test ! -e {NIX_DAEMON_SOCKET} && test -w /workspace && "
        "test ! -e /repo && test ! -e /corpus && test ! -e /reference && "
        "test ! -e /evaluator && test ! -e /results || exit 1; "
        "probe=/workspace/.nixbench-isolation-probe; : > \"$probe\" || exit 1; "
    )
    if not record_preflight:
        return checks
    return checks + (
        f"printf '%s\\n' "
        "'generic_forbidden_surfaces_absent=true' "
        "'neutral_mounts=true' "
        "'workspace_writable=true' "
        "'nix_daemon_absent=true' "
        f"> /workspace/{PREFLIGHT_RECORD} || exit 1; "
    )
