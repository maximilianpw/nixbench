from __future__ import annotations

import datetime as dt
import json
import warnings
from pathlib import Path
from typing import Any, Sequence

from .reporting import (
    build_study_report,
    fixed_corpus_interval,
    normalize_task_observation,
)
from .runner import TaskRunResult

def estimate_95(
    values: Sequence[float],
    *,
    lower_bound: float | None = None,
    upper_bound: float | None = None,
) -> dict[str, float | int | None]:
    result = fixed_corpus_interval(
        values,
        included_ids=[str(index) for index in range(len(values))],
        display_bounds=(lower_bound, upper_bound),
    )
    interval = result["interval"]
    return {
        "n": result["n"],
        "mean": result["estimate"],
        "min": result["range"]["min"],
        "max": result["range"]["max"],
        "standard_deviation": result["standard_deviation"],
        "ci95_low": interval["display_low"] if interval is not None else None,
        "ci95_high": interval["display_high"] if interval is not None else None,
        "ci95_margin": interval["margin"] if interval is not None else None,
    }


def build_study_trial(
    run_id: str,
    results: Sequence[TaskRunResult],
    *,
    corpus_digest: str | None = None,
    configuration_id: str | None = None,
    task_digests: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not results:
        raise ValueError("a study trial must contain at least one task result")
    if any(result.measurement_status != "valid" for result in results):
        raise ValueError("a study trial may contain only valid measurements")
    if (corpus_digest is None) != (configuration_id is None):
        raise ValueError(
            "corpus_digest and configuration_id must be supplied together"
        )

    observations = [
        normalize_task_observation(
            result.to_json(),
            task_digest=(task_digests or {}).get(result.task_id),
        )
        for result in results
    ]
    if corpus_digest is not None and any(
        item.get("task_digest") is None for item in observations
    ):
        raise ValueError(
            "content-addressed study trials require every task digest"
        )
    aggregates = _derive_trial_aggregates(observations)

    trial = {
        "run_id": run_id,
        "created_at": min(result.created_at for result in results),
        "measurement_status": "valid",
        **aggregates,
        "scoring_schema": _common_scoring_schema(results),
        "observations": observations,
        "agent_status": _aggregate_agent_status(results),
    }
    if corpus_digest is not None and configuration_id is not None:
        trial["corpus_digest"] = corpus_digest
        trial["configuration_id"] = configuration_id
    return trial


def build_study_attempt(
    run_id: str,
    results: Sequence[TaskRunResult],
    *,
    expected_task_count: int,
    corpus_digest: str | None = None,
    configuration_id: str | None = None,
    task_digests: dict[str, str] | None = None,
    additional_exclusion_reasons: Sequence[str] = (),
) -> dict[str, Any]:
    if expected_task_count < 1:
        raise ValueError("expected_task_count must be positive")
    if (corpus_digest is None) != (configuration_id is None):
        raise ValueError(
            "corpus_digest and configuration_id must be supplied together"
        )
    incomplete = len(results) != expected_task_count
    invalid_reasons = list(
        dict.fromkeys(
            result.invalid_reason
            for result in results
            if result.measurement_status == "invalid" and result.invalid_reason
        )
    )
    extra_reasons = list(dict.fromkeys(additional_exclusion_reasons))
    if incomplete:
        measurement_status = "incomplete"
        exclusion_reasons = ["incomplete-task-set", *invalid_reasons, *extra_reasons]
    elif invalid_reasons or extra_reasons:
        measurement_status = "invalid"
        exclusion_reasons = [*invalid_reasons, *extra_reasons]
    else:
        measurement_status = "valid"
        exclusion_reasons = []

    attempt: dict[str, Any] = {
        "run_id": run_id,
        "created_at": (
            min(result.created_at for result in results)
            if results
            else dt.datetime.now(dt.timezone.utc).isoformat()
        ),
        "measurement_status": measurement_status,
        "included_in_trials": measurement_status == "valid",
        "exclusion_reasons": exclusion_reasons,
        "completed_task_count": len(results),
        "expected_task_count": expected_task_count,
        "tasks": [result.to_json() for result in results],
        "observations": [
            normalize_task_observation(
                result.to_json(),
                task_digest=(task_digests or {}).get(result.task_id),
            )
            for result in results
        ],
        "score": None,
        "max_score": None,
        "score_rate": None,
    }
    if measurement_status == "valid":
        trial = build_study_trial(
            run_id,
            results,
            corpus_digest=corpus_digest,
            configuration_id=configuration_id,
            task_digests=task_digests,
        )
        attempt.update(
            {
                "score": trial["score"],
                "max_score": trial["max_score"],
                "score_rate": trial["score_rate"],
                "scoring_schema": trial["scoring_schema"],
            }
        )
    if corpus_digest is not None and configuration_id is not None:
        attempt["corpus_digest"] = corpus_digest
        attempt["configuration_id"] = configuration_id
    return attempt


def write_study_summary(
    results_dir: Path,
    study_id: str,
    trials: Sequence[dict[str, Any]],
    *,
    metadata: dict[str, Any] | None = None,
    attempts: Sequence[dict[str, Any]] | None = None,
    task_count: int | None = None,
) -> Path:
    if not trials and attempts is None:
        raise ValueError("a study must contain at least one trial")
    if trials:
        task_counts = {trial["task_count"] for trial in trials}
        if len(task_counts) != 1:
            raise ValueError("all study trials must use the same task count")
        derived_task_count = int(next(iter(task_counts)))
        if task_count is not None and task_count != derived_task_count:
            raise ValueError("task_count does not match study trials")
        task_count = derived_task_count
    elif task_count is None or task_count < 1:
        raise ValueError("task_count is required when no valid trials exist")
    identity_records = list(trials) if trials else list(attempts or [])
    identity_pairs = {
        (record.get("corpus_digest"), record.get("configuration_id"))
        for record in identity_records
    }
    if identity_pairs != {(None, None)}:
        if any(None in pair for pair in identity_pairs):
            raise ValueError("all study trials must include both identity fields")
        if len(identity_pairs) != 1:
            raise ValueError(
                "all study trials must use the same corpus_digest and configuration_id"
            )
        corpus_digest, configuration_id = next(iter(identity_pairs))
        metadata_values = metadata or {}
        if metadata_values.get("corpus_digest") != corpus_digest:
            raise ValueError("study metadata corpus_digest does not match its trials")
        if metadata_values.get("configuration_id") != configuration_id:
            raise ValueError("study metadata configuration_id does not match its trials")
    for trial in trials:
        _assert_trial_consistency(trial)

    estimates = (
        {
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
        }
        if trials
        else {}
    )
    summary = {
        "schema_version": 3,
        "study_id": study_id,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "metadata": metadata or {},
        "trial_count": len(trials),
        "task_count": task_count,
        "trials": list(trials),
        "estimates": estimates,
    }
    if attempts is not None:
        summary["attempt_count"] = len(attempts)
        summary["attempts"] = list(attempts)
    summary["report"] = build_study_report(summary)

    study_dir = results_dir / "studies" / study_id
    study_dir.mkdir(parents=True, exist_ok=True)
    summary_path = study_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return summary_path


def _common_scoring_schema(results: Sequence[TaskRunResult]) -> str:
    schemas = {result.scoring_schema for result in results}
    if len(schemas) != 1:
        raise ValueError("a study trial cannot mix scoring schemas")
    return next(iter(schemas))


def _aggregate_agent_status(
    results: Sequence[TaskRunResult],
) -> dict[str, Any] | None:
    statuses = [result.agent_status for result in results]
    if any(not isinstance(status, dict) for status in statuses):
        return None
    evidence = {
        str(status.get("preflight_evidence"))
        for status in statuses
        if isinstance(status, dict)
    }
    return {
        "task_count": len(results),
        "preflight_successful": all(
            status.get("preflight_successful") is True
            for status in statuses
            if isinstance(status, dict)
        ),
        "completed": all(
            status.get("completed") is True
            for status in statuses
            if isinstance(status, dict)
        ),
        "preflight_evidence": next(iter(evidence)) if len(evidence) == 1 else None,
    }


def _derive_trial_aggregates(
    observations: Sequence[dict[str, Any]],
) -> dict[str, int | float]:
    if not observations:
        raise ValueError("a study trial must contain at least one observation")
    if any(item.get("measurement_status") != "valid" for item in observations):
        raise ValueError("a study trial may contain only valid observations")
    task_count = len(observations)
    score = sum(float(item["score"]) for item in observations)
    max_score = sum(float(item["max_score"]) for item in observations)
    agent_time = sum(float(item["agent_duration_seconds"]) for item in observations)
    return {
        "passed_tasks": sum(item.get("passed") is True for item in observations),
        "failed_tasks": sum(item.get("passed") is not True for item in observations),
        "task_count": task_count,
        "score": score,
        "max_score": max_score,
        "score_rate": score / max_score if max_score else 0.0,
        "agent_time_seconds": agent_time,
        "agent_seconds_per_task": agent_time / task_count,
        "timeouts": sum(item.get("agent_timeout") is True for item in observations),
    }


def _assert_trial_consistency(trial: dict[str, Any]) -> None:
    observations = trial.get("observations")
    if not isinstance(observations, list):
        raise ValueError("new study trials require task observations")
    if not all(isinstance(item, dict) for item in observations):
        raise ValueError("trial observations must be objects")
    derived = _derive_trial_aggregates(observations)
    for key, expected in derived.items():
        actual = trial.get(key)
        if isinstance(expected, float):
            matches = isinstance(actual, (int, float)) and not isinstance(actual, bool) and abs(float(actual) - expected) <= 1e-12
        else:
            matches = actual == expected
        if not matches:
            raise ValueError(f"trial {trial.get('run_id')} has inconsistent {key}")


def count_study_trials(
    results_dir: Path,
    *,
    configuration_id: str | None = None,
    corpus_digest: str | None = None,
    series: str | None = None,
    effort: str | None = None,
    task_count: int | None = None,
) -> int:
    use_identity = configuration_id is not None or corpus_digest is not None
    if use_identity:
        if not configuration_id or not corpus_digest:
            raise ValueError(
                "configuration_id and corpus_digest must be supplied together"
            )
    else:
        if not series or not effort or task_count is None:
            raise ValueError(
                "use configuration_id and corpus_digest, or supply the deprecated "
                "series, effort, and task_count fields"
            )
        warnings.warn(
            "series/effort/task_count study counting is deprecated; use content identities",
            DeprecationWarning,
            stacklevel=2,
        )

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
        if use_identity:
            if (
                metadata.get("configuration_id") != configuration_id
                or metadata.get("corpus_digest") != corpus_digest
            ):
                continue
        elif (
            metadata.get("series") != series
            or metadata.get("effort") != effort
            or summary.get("task_count") != task_count
        ):
            continue

        trial_count = summary.get("trial_count")
        if (
            not isinstance(trial_count, int)
            or isinstance(trial_count, bool)
            or trial_count < 0
        ):
            raise ValueError(f"study summary {summary_path} has an invalid trial_count")
        total += trial_count

    return total
