from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .runner import TaskRunResult, SolutionMode, detect_nix_system, make_run_id, run_task, write_summary
from .task import Task, TaskError, find_task, iter_tasks


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except (TaskError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run NixBench AI Nix-code benchmark tasks.")
    parser.add_argument("--tasks-dir", type=Path, default=Path("tasks"), help="Task corpus directory.")
    parser.add_argument("--results-dir", type=Path, default=Path("results"), help="Result artifact directory.")
    parser.add_argument("--system", default=detect_nix_system(), help="Nix system to select tasks for.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List available benchmark tasks.")
    list_parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    list_parser.set_defaults(func=cmd_list)

    run_parser = subparsers.add_parser("run", help="Run one benchmark task.")
    run_parser.add_argument("task_id", help="Task id or directory name.")
    add_run_options(run_parser)
    run_parser.set_defaults(func=cmd_run)

    run_all_parser = subparsers.add_parser("run-all", help="Run all benchmark tasks for the selected system.")
    add_run_options(run_all_parser)
    run_all_parser.set_defaults(func=cmd_run_all)

    validate_parser = subparsers.add_parser("validate", help="Run task evaluators against starter or reference solutions.")
    validate_parser.add_argument("--solution", choices=["starter", "reference"], default="reference")
    validate_parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary work directories.")
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--agent-cmd", help="Shell command that edits the copied task workdir.")
    parser.add_argument(
        "--solution",
        choices=["agent", "starter", "reference"],
        default="agent",
        help="What to evaluate: an agent run, the starter files, or the reference solution.",
    )
    parser.add_argument("--agent-timeout-seconds", type=int, default=300)
    parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary work directories.")


def cmd_list(args: argparse.Namespace) -> int:
    tasks = [task for task in iter_tasks(args.tasks_dir) if task.supports_system(args.system)]
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": task.id,
                        "name": task.name,
                        "category": task.category,
                        "difficulty": task.difficulty,
                        "systems": task.systems,
                        "timeout_seconds": task.timeout_seconds,
                    }
                    for task in tasks
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    print(f"{'ID':34} {'CATEGORY':18} {'DIFFICULTY':10} NAME")
    for task in tasks:
        print(f"{task.id:34} {task.category:18} {task.difficulty:10} {task.name}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    _ensure_results_outside_tasks(args)
    task = find_task(args.tasks_dir, args.task_id)
    if not task.supports_system(args.system):
        raise ValueError(f"{task.id} does not support {args.system}; no task was run")

    run_id = make_run_id()
    result = run_task(
        task,
        results_dir=args.results_dir,
        run_id=run_id,
        solution_mode=_solution_mode(args.solution),
        agent_cmd=args.agent_cmd,
        agent_timeout_seconds=args.agent_timeout_seconds,
        keep_workdir=args.keep_workdir,
    )
    write_summary(args.results_dir, run_id, [result])
    _print_result(result)
    return 0 if result.passed else 1


def cmd_run_all(args: argparse.Namespace) -> int:
    tasks = _tasks_for_execution(args)
    run_id = make_run_id()
    results = []
    for task in tasks:
        result = run_task(
            task,
            results_dir=args.results_dir,
            run_id=run_id,
            solution_mode=_solution_mode(args.solution),
            agent_cmd=args.agent_cmd,
            agent_timeout_seconds=args.agent_timeout_seconds,
            keep_workdir=args.keep_workdir,
        )
        results.append(result)
        _print_result(result)

    summary_path = write_summary(args.results_dir, run_id, results)
    passed = sum(1 for result in results if result.passed)
    print(f"summary: {passed}/{len(results)} passed, wrote {summary_path}")
    return 0 if all(result.passed for result in results) else 1


def cmd_validate(args: argparse.Namespace) -> int:
    tasks = _tasks_for_execution(args)
    run_id = make_run_id()
    results = []
    expected_pass = args.solution == "reference"
    valid = 0
    for task in tasks:
        result = run_task(
            task,
            results_dir=args.results_dir,
            run_id=run_id,
            solution_mode=_solution_mode(args.solution),
            keep_workdir=args.keep_workdir,
        )
        results.append(result)
        actual = "PASS" if result.passed else "FAIL"
        expected = "PASS" if expected_pass else "FAIL"
        matches_expectation = _matches_validation_expectation(result, args.solution)
        valid += int(matches_expectation)
        status = "OK" if matches_expectation else "UNEXPECTED"
        print(
            f"{status} {result.task_id} expected={expected} actual={actual} "
            f"score={result.score:g}/{result.max_score:g} logs={result.result_dir}"
        )

    summary_path = write_summary(args.results_dir, run_id, results)
    print(
        f"validation: {valid}/{len(results)} {args.solution} outcomes matched expectations, "
        f"wrote {summary_path}"
    )
    return 0 if valid == len(results) else 1


def _tasks_for_execution(args: argparse.Namespace) -> list[Task]:
    _ensure_results_outside_tasks(args)
    tasks = [task for task in iter_tasks(args.tasks_dir) if task.supports_system(args.system)]
    if not tasks:
        raise ValueError(f"no tasks in {args.tasks_dir} support system {args.system}")
    return tasks


def _ensure_results_outside_tasks(args: argparse.Namespace) -> None:
    tasks_dir = args.tasks_dir.resolve()
    results_dir = args.results_dir.resolve()
    try:
        results_dir.relative_to(tasks_dir)
    except ValueError:
        return
    raise ValueError("--results-dir must be outside --tasks-dir")


def _matches_validation_expectation(result: TaskRunResult, solution: str) -> bool:
    if solution == "reference":
        return result.passed and result.score == result.max_score
    return (
        not result.passed
        and result.score_valid
        and not result.check.timed_out
        and result.check.returncode == 1
        and 0 <= result.score < result.max_score
    )


def _solution_mode(value: str) -> SolutionMode:
    if value not in {"agent", "starter", "reference"}:
        raise ValueError(f"invalid solution mode: {value}")
    return value  # type: ignore[return-value]


def _print_result(result) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"{status} {result.task_id} score={result.score:g}/{result.max_score:g} logs={result.result_dir}")
