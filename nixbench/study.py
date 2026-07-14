from __future__ import annotations

import datetime as dt
import json
import math
import statistics
from pathlib import Path
from typing import Any, Sequence

from .runner import TaskRunResult


# Two-sided 95% Student's t critical values. Small benchmark studies need the
# wider t interval rather than the large-sample 1.96 shortcut.
T_CRITICAL_95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    21: 2.080,
    22: 2.074,
    23: 2.069,
    24: 2.064,
    25: 2.060,
    26: 2.056,
    27: 2.052,
    28: 2.048,
    29: 2.045,
    30: 2.042,
}


def estimate_95(
    values: Sequence[float],
    *,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> dict[str, float | int | None]:
    if not values:
        raise ValueError("cannot estimate an empty sample")

    sample = [float(value) for value in values]
    mean = statistics.fmean(sample)
    standard_deviation = statistics.stdev(sample) if len(sample) > 1 else None
    margin = None
    if standard_deviation is not None:
        degrees_of_freedom = len(sample) - 1
        critical = T_CRITICAL_95.get(degrees_of_freedom, 1.96)
        margin = critical * standard_deviation / math.sqrt(len(sample))

    ci_low = mean - margin if margin is not None else None
    ci_high = mean + margin if margin is not None else None
    if ci_low is not None and lower_bound is not None:
        ci_low = max(lower_bound, ci_low)
    if ci_high is not None and upper_bound is not None:
        ci_high = min(upper_bound, ci_high)

    return {
        "n": len(sample),
        "mean": mean,
        "min": min(sample),
        "max": max(sample),
        "standard_deviation": standard_deviation,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "ci95_margin": margin,
    }


def build_study_trial(run_id: str, results: Sequence[TaskRunResult]) -> dict[str, Any]:
    if not results:
        raise ValueError("a study trial must contain at least one task result")

    agent_time_seconds = sum(
        result.agent.duration_seconds for result in results if result.agent is not None
    )
    total_score = sum(result.score for result in results)
    total_max_score = sum(result.max_score for result in results)
    task_count = len(results)

    return {
        "run_id": run_id,
        "created_at": min(result.created_at for result in results),
        "passed_tasks": sum(1 for result in results if result.passed),
        "failed_tasks": sum(1 for result in results if not result.passed),
        "task_count": task_count,
        "score": total_score,
        "max_score": total_max_score,
        "score_rate": total_score / total_max_score if total_max_score else 0.0,
        "agent_time_seconds": agent_time_seconds,
        "agent_seconds_per_task": agent_time_seconds / task_count,
        "timeouts": sum(
            1
            for result in results
            if result.agent is not None and result.agent.timed_out
        ),
    }


def write_study_summary(
    results_dir: Path,
    study_id: str,
    trials: Sequence[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
) -> Path:
    if not trials:
        raise ValueError("a study must contain at least one trial")

    task_counts = {trial["task_count"] for trial in trials}
    if len(task_counts) != 1:
        raise ValueError("all study trials must use the same task count")
    task_count = int(next(iter(task_counts)))

    summary = {
        "schema_version": 1,
        "study_id": study_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "metadata": metadata or {},
        "trial_count": len(trials),
        "task_count": task_count,
        "trials": list(trials),
        "estimates": {
            "passed_tasks": estimate_95(
                [float(trial["passed_tasks"]) for trial in trials],
                lower_bound=0,
                upper_bound=task_count,
            ),
            "score_rate": estimate_95(
                [float(trial["score_rate"]) for trial in trials],
                lower_bound=0,
                upper_bound=1,
            ),
            "agent_time_seconds": estimate_95(
                [float(trial["agent_time_seconds"]) for trial in trials],
                lower_bound=0,
            ),
            "agent_seconds_per_task": estimate_95(
                [float(trial["agent_seconds_per_task"]) for trial in trials],
                lower_bound=0,
            ),
        },
    }

    study_dir = results_dir / "studies" / study_id
    study_dir.mkdir(parents=True, exist_ok=True)
    summary_path = study_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return summary_path


def count_study_trials(
    results_dir: Path,
    *,
    series: str,
    effort: str,
    task_count: int,
) -> int:
    total = 0
    for summary_path in sorted((results_dir / "studies").glob("*/summary.json")):
        try:
            summary = json.loads(summary_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"cannot read study summary {summary_path}: {exc}"
            ) from exc

        metadata = summary.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"study summary {summary_path} has no metadata object")
        if metadata.get("publish") is False:
            continue
        if (
            metadata.get("series") != series
            or metadata.get("effort") != effort
            or summary.get("task_count") != task_count
        ):
            continue

        trial_count = summary.get("trial_count")
        if (
            not isinstance(trial_count, int)
            or isinstance(trial_count, bool)
            or trial_count < 1
        ):
            raise ValueError(f"study summary {summary_path} has an invalid trial_count")
        total += trial_count

    return total
