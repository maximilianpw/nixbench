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

from .adapters import get_trusted_adapter
from .agent_status import read_agent_status
from .scoring import Criterion, score_schema_two_payload
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
    measurement_status: str
    task_outcome: str | None
    invalid_reason: str | None
    scoring_schema: str
    criteria: dict[str, bool]
    failure_classes: list[str]
    infrastructure_events: list[str]
    completion_attestation: str
    agent_status: dict[str, Any] | None

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
    completion_attestation: Literal["required", "unattested"] = "unattested",
    agent_adapter: str | None = None,
    wrapper_prompt_path: Path | None = None,
    isolation_profile: str | None = None,
    network_policy: str | None = None,
    corpus_root: Path | None = None,
) -> TaskRunResult:
    if solution_mode == "agent" and not agent_cmd:
        raise ValueError("agent solution mode requires --agent-cmd")

    result_dir = results_dir / run_id / task.id
    result_dir.mkdir(parents=True, exist_ok=True)

    isolated_run = solution_mode == "agent" and isolation_profile is not None
    temp_prefix = "nixbench-isolated-" if isolated_run else f"nixbench-{task.id}-"
    temp_parent = Path(
        tempfile.mkdtemp(
            prefix=temp_prefix,
            dir="/tmp" if isolated_run else None,
        )
    )
    workdir = temp_parent / "work"
    original_dir = temp_parent / "original"

    shutil.copytree(task.starter_dir, workdir)
    shutil.copytree(task.starter_dir, original_dir)
    shutil.copy2(task.prompt_path, workdir / "NIXBENCH_PROMPT.md")
    shutil.copy2(task.prompt_path, original_dir / "NIXBENCH_PROMPT.md")

    if solution_mode == "reference":
        _copy_overlay(task.reference_dir, workdir)

    score_file = (result_dir / "score.json").resolve()
    attestation_dir = Path(tempfile.mkdtemp(prefix="nixbench-attestation-"))
    agent_status_file = attestation_dir / "status.json"
    agent_env, evaluator_env = _build_command_envs(
        task=task,
        workdir=workdir,
        score_file=score_file,
        agent_status_file=(
            agent_status_file
            if completion_attestation == "required" and agent_adapter is not None
            else None
        ),
        extra_env=extra_env,
    )

    agent_result: CommandResult | None = None
    parsed_agent_status = None
    agent_status_error: str | None = None
    if solution_mode == "agent":
        if agent_adapter is None:
            agent_result = _run_shell_command(
                agent_cmd or "",
                cwd=workdir,
                env=agent_env,
                timeout_seconds=agent_timeout_seconds,
                log_path=result_dir / "agent.log",
            )
        else:
            adapter = get_trusted_adapter(agent_adapter)
            adapter_options: dict[str, Any] = {}
            if adapter.isolation_profile is not None:
                if isolation_profile != adapter.isolation_profile:
                    raise ValueError(
                        "trusted isolation adapter does not match the resolved protocol"
                    )
                adapter_options = {
                    "workspace": workdir,
                    "network_policy": network_policy,
                }
            agent_result = _run_exec_command(
                adapter.command(
                    agent_cmd or "",
                    wrapper_prompt_path=wrapper_prompt_path,
                    **adapter_options,
                ),
                cwd=workdir,
                env=agent_env,
                timeout_seconds=agent_timeout_seconds,
                log_path=result_dir / "agent.log",
            )
        if completion_attestation == "required":
            parsed_agent_status, agent_status_error = read_agent_status(agent_status_file)
        agent_status_file.unlink(missing_ok=True)
        shutil.rmtree(attestation_dir, ignore_errors=True)
    else:
        shutil.rmtree(attestation_dir, ignore_errors=True)

    score_file.unlink(missing_ok=True)

    workspace_escape = (
        solution_mode == "agent"
        and isolation_profile is not None
        and _workspace_symlink_escapes(workdir)
    )
    if workspace_escape:
        check_log = result_dir / "check.log"
        check_log.write_text(
            "Evaluator not run because the workspace contains an escaping symlink.\n",
            encoding="utf-8",
        )
        check_result = CommandResult(
            command="evaluator not run: workspace-escape",
            returncode=2,
            duration_seconds=0.0,
            timed_out=False,
            log_path=str(check_log),
        )
    else:
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
    default_passed = check_passed and not agent_timed_out
    score, score_detail, score_is_valid = _read_score(
        score_file,
        default_score=task.max_score if default_passed else 0.0,
        max_score=task.max_score,
        criteria=task.criteria,
    )
    measurement_status = "valid"
    invalid_reason: str | None = None
    infrastructure_events: list[str] = []
    if workspace_escape:
        measurement_status = "invalid"
        invalid_reason = "workspace-escape"
        infrastructure_events.append("workspace-escape")
    elif check_result.timed_out:
        measurement_status = "invalid"
        invalid_reason = "evaluator-timeout"
        infrastructure_events.append("evaluator-timeout")
    elif check_result.returncode not in {0, 1}:
        measurement_status = "invalid"
        invalid_reason = "evaluator-error"
        infrastructure_events.append("evaluator-error")
    elif not score_is_valid:
        measurement_status = "invalid"
        invalid_reason = "invalid-score-payload"
        infrastructure_events.append("invalid-score-payload")
    elif task.criteria and score_detail is not None:
        required_passed = score_detail.get("required_passed") is True
        if (check_result.returncode == 0) != required_passed:
            measurement_status = "invalid"
            invalid_reason = "exit-criteria-disagreement"
            infrastructure_events.append("exit-criteria-disagreement")

    if (
        measurement_status == "valid"
        and agent_result is not None
        and not agent_result.timed_out
        and agent_result.returncode != 0
    ):
        measurement_status = "invalid"
        invalid_reason = "agent-process-error"
        infrastructure_events.append("agent-process-error")

    agent_status = None
    if solution_mode == "agent" and completion_attestation == "required":
        parsed_status, status_error = parsed_agent_status, agent_status_error
        if parsed_status is not None:
            agent_status = parsed_status.to_json()
        if measurement_status == "valid" and status_error is not None:
            measurement_status = "invalid"
            invalid_reason = status_error
            infrastructure_events.append(status_error)
        elif measurement_status == "valid" and parsed_status is not None:
            if not parsed_status.preflight_successful:
                measurement_status = "invalid"
                invalid_reason = "agent-preflight-failed"
                infrastructure_events.append("agent-preflight-failed")
            elif not agent_timed_out and parsed_status.transport_error is not None:
                measurement_status = "invalid"
                invalid_reason = "agent-transport-error"
                infrastructure_events.append("agent-transport-error")
            elif not agent_timed_out and not parsed_status.completed:
                measurement_status = "invalid"
                invalid_reason = "agent-completion-missing"
                infrastructure_events.append("agent-completion-missing")
            elif not agent_timed_out and (
                agent_result is None
                or parsed_status.launcher_exit != agent_result.returncode
            ):
                measurement_status = "invalid"
                invalid_reason = "agent-exit-mismatch"
                infrastructure_events.append("agent-exit-mismatch")
    elif solution_mode == "agent":
        infrastructure_events.append("unattested-agent")

    if measurement_status != "valid":
        task_outcome = None
    elif agent_timed_out:
        task_outcome = "agent-timeout"
    elif check_result.returncode == 0:
        task_outcome = "pass"
    else:
        task_outcome = "fail"
    passed = measurement_status == "valid" and task_outcome == "pass"
    normalized_criteria = (
        dict(score_detail.get("criteria", {}))
        if score_detail is not None and score_detail.get("format") == "criteria-v2"
        else {}
    )
    failure_classes = (
        list(score_detail.get("failure_classes", []))
        if score_detail is not None and score_detail.get("format") == "criteria-v2"
        else []
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
        score_valid=score_is_valid,
        score_detail=score_detail,
        measurement_status=measurement_status,
        task_outcome=task_outcome,
        invalid_reason=invalid_reason,
        scoring_schema=task.scoring_schema,
        criteria=normalized_criteria,
        failure_classes=failure_classes,
        infrastructure_events=infrastructure_events,
        completion_attestation=(
            completion_attestation if solution_mode == "agent" else "not-required"
        ),
        agent_status=agent_status,
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
    agent_status_file: Path | None,
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
    agent_env.pop("NIXBENCH_AGENT_STATUS_FILE", None)
    agent_env.pop("NIXBENCH_EVALUATOR_EXIT", None)
    agent_env.update(public_env)
    if agent_status_file is not None:
        agent_env["NIXBENCH_AGENT_STATUS_FILE"] = str(agent_status_file)

    evaluator_env = base_env.copy()
    evaluator_env.pop("NIXBENCH_AGENT_STATUS_FILE", None)
    evaluator_env.update(public_env)
    evaluator_env.update(
        {
            "NIXBENCH_TASK_DIR": str(task.root),
            "NIXBENCH_SCORE_FILE": str(score_file),
            "NIXBENCH_EVALUATOR_EXIT": str(
                Path(__file__).with_name("evaluator_exit.py")
            ),
        }
    )

    return agent_env, evaluator_env


def write_summary(
    results_dir: Path,
    run_id: str,
    results: list[TaskRunResult],
    *,
    metadata: dict[str, Any] | None = None,
) -> Path:
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
        "metadata": metadata or {},
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


def _workspace_symlink_escapes(workdir: Path) -> bool:
    root = workdir.resolve()
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        for name in [*directory_names, *file_names]:
            path = Path(directory) / name
            if not path.is_symlink():
                continue
            try:
                path.resolve(strict=False).relative_to(root)
            except (OSError, RuntimeError, ValueError):
                return True
    return False


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
    criteria: tuple[Criterion, ...] = (),
) -> tuple[float, dict[str, Any] | None, bool]:
    try:
        score_stat = score_file.lstat()
    except FileNotFoundError:
        if criteria:
            return (
                0.0,
                {"format": "invalid", "error": "missing criteria-v2 score file"},
                False,
            )
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

    if criteria:
        try:
            score, detail = score_schema_two_payload(parsed, criteria)
        except ValueError as exc:
            return 0.0, {"format": "invalid", "error": str(exc)}, False
        return score, detail, True

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
