from __future__ import annotations

import datetime as dt
import difflib
import json
import math
import os
import platform
import shutil
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

    score_file = result_dir / "score.json"
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
    score, score_detail = _read_score(
        score_file,
        default_score=task.max_score if passed else 0.0,
        max_score=task.max_score,
    )

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
        score_detail=score_detail,
    )

    result_path = result_dir / "result.json"
    result_path.write_text(json.dumps(result.to_json(), indent=2, sort_keys=True) + "\n")

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
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
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

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=shell,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout_seconds,
            check=False,
        )
        output = completed.stdout
        returncode = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        output += f"\nTimed out after {timeout_seconds} seconds.\n"
        returncode = 124

    duration = time.monotonic() - start
    log_path.write_text(output)
    return CommandResult(
        command=display_command,
        returncode=returncode,
        duration_seconds=round(duration, 3),
        timed_out=timed_out,
        log_path=str(log_path),
    )


def _read_score(
    score_file: Path,
    *,
    default_score: float,
    max_score: float,
) -> tuple[float, dict[str, Any] | None]:
    if not score_file.exists():
        return default_score, None

    text = score_file.read_text().strip()
    if not text:
        return default_score, None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        score = _coerce_score(text, max_score=max_score)
        if score is None:
            return default_score, {"format": "invalid", "raw": text}
        return score, {"format": "plain"}

    if isinstance(parsed, dict) and "score" in parsed:
        score = _coerce_score(parsed["score"], max_score=max_score)
        if score is None:
            return default_score, parsed
        return score, parsed

    score = _coerce_score(parsed, max_score=max_score)
    if score is not None:
        return score, {"format": "json-number"}

    return default_score, {"format": "unsupported", "raw": parsed}


def _coerce_score(value: Any, *, max_score: float) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(score):
        return None

    return max(0.0, min(score, max_score))


def _write_unified_dir_diff(original: Path, changed: Path, output_path: Path) -> None:
    lines: list[str] = []
    files = sorted(_relative_files(original) | _relative_files(changed))

    for rel_path in files:
        old_path = original / rel_path
        new_path = changed / rel_path
        old_lines = _read_text_lines(old_path)
        new_lines = _read_text_lines(new_path)
        if old_lines == new_lines:
            continue

        lines.extend(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{rel_path}",
                tofile=f"b/{rel_path}",
                lineterm="",
            )
        )
        lines.append("")

    output_path.write_text("\n".join(lines))


def _relative_files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in root.rglob("*") if path.is_symlink() or path.is_file()}


def _read_text_lines(path: Path) -> list[str]:
    if path.is_symlink():
        try:
            target = os.readlink(path)
        except OSError:
            target = "<unreadable>"
        return [f"<symlink -> {target}>"]

    if not path.exists():
        return []

    try:
        size = path.stat().st_size
    except OSError:
        return ["<unreadable file>"]

    if size > MAX_DIFF_TEXT_BYTES:
        return [f"<large file: {size} bytes>"]

    try:
        return path.read_text().splitlines()
    except UnicodeDecodeError:
        return ["<binary file>"]
