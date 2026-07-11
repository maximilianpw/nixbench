from __future__ import annotations

import datetime as dt
import difflib
import json
import math
import os
import platform
import signal
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from .task import Task

SolutionMode = Literal["agent", "starter", "reference"]
MAX_DIFF_TEXT_BYTES = 1_000_000
MAX_SCORE_FILE_BYTES = 1_000_000


@dataclass
class CommandResult:
    command: str
    returncode: int
    duration_seconds: float
    timed_out: bool
    log_path: str


@dataclass
class TaskRunResult:
    task_id: str
    name: str
    category: str
    difficulty: str
    solution_mode: str
    passed: bool
    score: float
    max_score: float
    created_at: str
    workdir: str | None
    result_dir: str
    diff_path: str
    agent: CommandResult | None
    check: CommandResult
    score_valid: bool
    score_detail: dict[str, Any] | None

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        return data


def detect_nix_system() -> str:
    machine = platform.machine().lower()
    os_name = platform.system().lower()

    arch = {
        "arm64": "aarch64",
        "aarch64": "aarch64",
        "x86_64": "x86_64",
        "amd64": "x86_64",
    }.get(machine, machine)

    system = {
        "darwin": "darwin",
        "linux": "linux",
    }.get(os_name, os_name)

    return f"{arch}-{system}"


def make_run_id() -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def run_task(
    task: Task,
    *,
    results_dir: Path,
    run_id: str,
    solution_mode: SolutionMode,
    agent_cmd: str | None = None,
    agent_timeout_seconds: int = 300,
    keep_workdir: bool = False,
    extra_env: dict[str, str] | None = None,
) -> TaskRunResult:
    if solution_mode == "agent" and not agent_cmd:
        raise ValueError("agent solution mode requires --agent-cmd")

    result_dir = results_dir / run_id / task.id
    result_dir.mkdir(parents=True, exist_ok=True)

    temp_parent = Path(tempfile.mkdtemp(prefix=f"nixbench-{task.id}-"))
    workdir = temp_parent / "work"
    original_dir = temp_parent / "original"

    shutil.copytree(task.starter_dir, workdir)
    shutil.copytree(task.starter_dir, original_dir)
    shutil.copy2(task.prompt_path, workdir / "NIXBENCH_PROMPT.md")
    shutil.copy2(task.prompt_path, original_dir / "NIXBENCH_PROMPT.md")

    if solution_mode == "reference":
        _copy_overlay(task.reference_dir, workdir)

    score_file = (result_dir / "score.json").resolve()
    agent_env, evaluator_env = _build_command_envs(
        task=task,
        workdir=workdir,
        score_file=score_file,
        extra_env=extra_env,
    )

    agent_result: CommandResult | None = None
    if solution_mode == "agent":
        agent_result = _run_shell_command(
            agent_cmd or "",
            cwd=workdir,
            env=agent_env,
            timeout_seconds=agent_timeout_seconds,
            log_path=result_dir / "agent.log",
        )

    score_file.unlink(missing_ok=True)

    check_result = _run_exec_command(
        ["/bin/sh", str(task.evaluator_path), str(workdir)],
        cwd=workdir,
        env=evaluator_env,
        timeout_seconds=task.timeout_seconds,
        log_path=result_dir / "check.log",
    )

    diff_path = result_dir / "diff.patch"
    _write_unified_dir_diff(original_dir, workdir, diff_path)

    agent_timed_out = agent_result.timed_out if agent_result is not None else False
    check_passed = check_result.returncode == 0 and not check_result.timed_out
    passed = check_passed and not agent_timed_out
    score, score_detail, score_is_valid = _read_score(
        score_file,
        default_score=task.max_score if passed else 0.0,
        max_score=task.max_score,
    )
    if not score_is_valid:
        passed = False

    result = TaskRunResult(
        task_id=task.id,
        name=task.name,
        category=task.category,
        difficulty=task.difficulty,
        solution_mode=solution_mode,
        passed=passed,
        score=score,
        max_score=task.max_score,
        created_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        workdir=str(workdir) if keep_workdir else None,
        result_dir=str(result_dir),
        diff_path=str(diff_path),
        agent=agent_result,
        check=check_result,
        score_valid=score_is_valid,
        score_detail=score_detail,
    )

    result_path = result_dir / "result.json"
    result_path.write_text(json.dumps(result.to_json(), indent=2, sort_keys=True, allow_nan=False) + "\n")

    if not keep_workdir:
        shutil.rmtree(temp_parent, ignore_errors=True)

    return result


def _build_command_envs(
    *,
    task: Task,
    workdir: Path,
    score_file: Path,
    extra_env: dict[str, str] | None,
) -> tuple[dict[str, str], dict[str, str]]:
    base_env = os.environ.copy()
    if extra_env:
        base_env.update(extra_env)

    public_env = {
        "NIXBENCH_TASK_ID": task.id,
        "NIXBENCH_WORKDIR": str(workdir),
        "NIXBENCH_PROMPT": str(workdir / "NIXBENCH_PROMPT.md"),
    }

    agent_env = base_env.copy()
    agent_env.pop("NIXBENCH_TASK_DIR", None)
    agent_env.pop("NIXBENCH_SCORE_FILE", None)
    agent_env.update(public_env)

    evaluator_env = base_env.copy()
    evaluator_env.update(public_env)
    evaluator_env.update(
        {
            "NIXBENCH_TASK_DIR": str(task.root),
            "NIXBENCH_SCORE_FILE": str(score_file),
        }
    )

    return agent_env, evaluator_env


def write_summary(results_dir: Path, run_id: str, results: list[TaskRunResult]) -> Path:
    run_dir = results_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    total_score = sum(result.score for result in results)
    total_max = sum(result.max_score for result in results)
    summary = {
        "run_id": run_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "passed": sum(1 for result in results if result.passed),
        "failed": sum(1 for result in results if not result.passed),
        "score": total_score,
        "max_score": total_max,
        "tasks": [result.to_json() for result in results],
    }
    summary_path = run_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return summary_path


def _copy_overlay(src: Path, dst: Path) -> None:
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _run_shell_command(
    command: str,
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    log_path: Path,
) -> CommandResult:
    return _run_subprocess(
        command,
        cwd=cwd,
        env=env,
        timeout_seconds=timeout_seconds,
        log_path=log_path,
        shell=True,
        display_command=command,
    )


def _run_exec_command(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    log_path: Path,
) -> CommandResult:
    return _run_subprocess(
        command,
        cwd=cwd,
        env=env,
        timeout_seconds=timeout_seconds,
        log_path=log_path,
        shell=False,
        display_command=" ".join(command),
    )


def _run_subprocess(
    command: str | list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    log_path: Path,
    shell: bool,
    display_command: str,
) -> CommandResult:
    start = time.monotonic()
    timed_out = False
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryFile() as output_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            _terminate_process_group(process)
        except BaseException:
            _terminate_process_group(process)
            raise
        else:
            _kill_process_group(process)

        output_file.seek(0)
        output_bytes = output_file.read()

    output = (output_bytes or b"").decode("utf-8", errors="replace")
    returncode = process.returncode
    if timed_out:
        output += f"\nTimed out after {timeout_seconds} seconds.\n"
        returncode = 124

    duration = time.monotonic() - start
    log_path.write_text(output, encoding="utf-8")
    return CommandResult(
        command=display_command,
        returncode=returncode,
        duration_seconds=round(duration, 3),
        timed_out=timed_out,
        log_path=str(log_path),
    )


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        if process.poll() is None:
            process.kill()


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    _kill_process_group(process)
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _read_score(
    score_file: Path,
    *,
    default_score: float,
    max_score: float,
) -> tuple[float, dict[str, Any] | None, bool]:
    try:
        score_stat = score_file.lstat()
    except FileNotFoundError:
        return _clamp_score(default_score, max_score), None, True
    except OSError as exc:
        return 0.0, {"format": "invalid", "error": type(exc).__name__}, False

    if not stat.S_ISREG(score_stat.st_mode):
        return 0.0, {"format": "invalid", "error": "score path must be a regular file"}, False

    try:
        if score_stat.st_size > MAX_SCORE_FILE_BYTES:
            return 0.0, {"format": "invalid", "error": "score file is too large"}, False
        text = score_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as exc:
        return 0.0, {"format": "invalid", "error": type(exc).__name__}, False
    if not text:
        return 0.0, {"format": "invalid", "error": "empty score file"}, False

    try:
        parsed = json.loads(text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ValueError, RecursionError):
        return 0.0, {"format": "invalid", "error": "invalid JSON"}, False
    try:
        json_safe = _is_json_safe(parsed)
    except RecursionError:
        json_safe = False
    if not json_safe:
        return 0.0, {"format": "invalid", "error": "score payload contains non-finite numbers"}, False

    if isinstance(parsed, dict) and "score" in parsed:
        score = _coerce_score(parsed["score"], max_score=max_score)
        if score is None:
            return (
                0.0,
                {"format": "invalid", "error": "score must be a finite JSON number"},
                False,
            )
        return score, parsed, True

    score = _coerce_score(parsed, max_score=max_score)
    if score is not None:
        return score, {"format": "json-number"}, True

    return (
        0.0,
        {"format": "invalid", "error": "score payload must be a JSON number or object with score"},
        False,
    )


def _clamp_score(score: float, max_score: float) -> float:
    return max(0.0, min(score, max_score))


def _coerce_score(value: Any, *, max_score: float) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        score = float(value)
    except OverflowError:
        return None
    if not math.isfinite(score):
        return None

    return max(0.0, min(score, max_score))


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _is_json_safe(value: Any) -> bool:
    if value is None or isinstance(value, str | bool | int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_is_json_safe(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_safe(item) for key, item in value.items())
    return False


def _write_unified_dir_diff(original: Path, changed: Path, output_path: Path) -> None:
    lines: list[str] = []
    files = sorted(_relative_files(original) | _relative_files(changed))

    for rel_path in files:
        old_path = original / rel_path
        new_path = changed / rel_path
        old_exists = _path_is_file_or_symlink(old_path)
        new_exists = _path_is_file_or_symlink(new_path)
        old_lines = _read_text_lines(old_path)
        new_lines = _read_text_lines(new_path)
        if old_exists == new_exists and old_lines == new_lines:
            continue

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{rel_path}" if old_exists else "/dev/null",
                tofile=f"b/{rel_path}" if new_exists else "/dev/null",
                lineterm="",
            )
        )
        if not diff_lines:
            diff_lines = [
                f"--- {'a/' + str(rel_path) if old_exists else '/dev/null'}",
                f"+++ {'b/' + str(rel_path) if new_exists else '/dev/null'}",
            ]
        lines.extend(diff_lines)
        lines.append("")

    output_path.write_text("\n".join(lines))


def _relative_files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if _path_is_file_or_symlink(path)}


def _path_is_file_or_symlink(path: Path) -> bool:
    return path.is_symlink() or path.is_file()


def _read_text_lines(path: Path) -> list[str]:
    if path.is_symlink():
        try:
            target = os.readlink(path)
        except OSError:
            target = "<unreadable>"
        return [f"<symlink -> {target}>"]

    if not path.exists():
        return []
    if not path.is_file():
        return []

    try:
        size = path.stat().st_size
    except OSError:
        return ["<unreadable file>"]

    if size > MAX_DIFF_TEXT_BYTES:
        return [f"<large file: {size} bytes>"]

    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return ["<binary file>"]
    except OSError:
        return ["<unreadable file>"]

    lines = text.splitlines()
    if text and not text.endswith(("\n", "\r")):
        lines.append("\\ No newline at end of file")
    return lines
