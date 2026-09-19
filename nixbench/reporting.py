from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from .scoring import FAILURE_CLASSES
from .study_validation import normalize_task_observation, validate_current_study
from .task import VALID_CATEGORIES


REPORT_SCHEMA_VERSION = 1
FIXED_CORPUS_METHOD_VERSION = "1"
WILSON_METHOD_VERSION = "1"
RESAMPLING_METHOD_VERSION = "1"
CORPUS_HEALTH_SCHEMA_VERSION = 1
RESAMPLING_REPLICATES = 10_000


# Two-sided 95% Student's t critical values. Values above 30 degrees of
# freedom use the normal approximation, matching the historical implementation.
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


def fixed_corpus_interval(
    values: Sequence[float],
    *,
    included_ids: Sequence[str],
    excluded_reasons: Mapping[str, str] | None = None,
    display_bounds: tuple[float | None, float | None] | None = None,
) -> dict[str, Any]:
    if not values:
        raise ValueError("cannot estimate an empty sample")
    if len(values) != len(included_ids):
        raise ValueError("included_ids must identify every sampled value")
    sample = [_finite_number(value, "sample value") for value in values]
    mean = statistics.fmean(sample)
    standard_deviation = statistics.stdev(sample) if len(sample) > 1 else None
    interval = None
    warnings: list[str] = []
    if standard_deviation is None:
        warnings.append("interval-requires-at-least-two-trials")
    else:
        critical = _t_critical_95(len(sample) - 1)
        margin = critical * standard_deviation / math.sqrt(len(sample))
        raw_low = mean - margin
        raw_high = mean + margin
        display_low = raw_low
        display_high = raw_high
        if display_bounds is not None:
            lower, upper = display_bounds
            if lower is not None:
                display_low = max(lower, display_low)
            if upper is not None:
                display_high = min(upper, display_high)
        interval = {
            "level": 0.95,
            "raw_low": raw_low,
            "raw_high": raw_high,
            "display_low": display_low,
            "display_high": display_high,
            "margin": margin,
        }
    if len(sample) < 5:
        warnings.append("fewer-than-five-trials")
    return {
        "method": "student-t-fixed-corpus-run-variation",
        "method_version": FIXED_CORPUS_METHOD_VERSION,
        "sampling_unit": "complete-corpus-trial",
        "n": len(sample),
        "included_ids": list(included_ids),
        "excluded_ids": sorted((excluded_reasons or {}).keys()),
        "exclusion_reasons": dict(sorted((excluded_reasons or {}).items())),
        "estimate": mean,
        "interval": interval,
        "standard_deviation": standard_deviation,
        "range": {"min": min(sample), "max": max(sample)},
        "warnings": warnings,
    }


def wilson_interval(
    successes: int,
    n: int,
    *,
    included_ids: Sequence[str],
    excluded_reasons: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if isinstance(successes, bool) or isinstance(n, bool):
        raise ValueError("Wilson counts must be integers")
    if successes < 0 or n < 1 or successes > n:
        raise ValueError("Wilson counts must satisfy 0 <= successes <= n")
    if len(included_ids) != n:
        raise ValueError("included_ids must identify every Bernoulli observation")
    z = 1.959963984540054
    proportion = successes / n
    denominator = 1 + z * z / n
    center = (proportion + z * z / (2 * n)) / denominator
    half_width = (
        z
        * math.sqrt(proportion * (1 - proportion) / n + z * z / (4 * n * n))
        / denominator
    )
    warnings = ["fewer-than-five-observations"] if n < 5 else []
    return {
        "method": "wilson-task-pass-stability",
        "method_version": WILSON_METHOD_VERSION,
        "sampling_unit": "valid-task-observation",
        "n": n,
        "included_ids": list(included_ids),
        "excluded_ids": sorted((excluded_reasons or {}).keys()),
        "exclusion_reasons": dict(sorted((excluded_reasons or {}).items())),
        "successes": successes,
        "estimate": proportion,
        "interval": {
            "level": 0.95,
            "low": center - half_width,
            "high": center + half_width,
        },
        "standard_deviation": None,
        "range": {"min": 0, "max": 1},
        "warnings": warnings,
    }


def resampling_sensitivity(
    trials: Sequence[Mapping[str, Any]],
    *,
    task_ids: Sequence[str],
    corpus_id: str,
    configuration_id: str,
    stratum_id: str,
) -> dict[str, Any]:
    ordered_tasks = sorted(set(task_ids))
    run_ids = [str(trial.get("run_id", "")) for trial in trials]
    base = {
        "method": "trial-task-resampling-sensitivity",
        "method_version": RESAMPLING_METHOD_VERSION,
        "sampling_unit": "complete-trial-and-fixed-corpus-task",
        "n": len(trials),
        "included_ids": run_ids,
        "excluded_ids": [],
        "exclusion_reasons": {},
        "estimate": None,
        "interval": None,
        "standard_deviation": None,
        "range": None,
        "warnings": [],
        "replicates": RESAMPLING_REPLICATES,
        "seed_sha256": _resampling_seed(
            corpus_id, configuration_id, stratum_id
        ),
        "unavailable_reason": None,
    }
    if len(ordered_tasks) < 5:
        base["unavailable_reason"] = "fewer-than-five-tasks"
        base["warnings"] = ["descriptive-only-stratum"]
        return base
    if not trials:
        base["unavailable_reason"] = "no-valid-trials"
        return base

    matrix: list[list[float]] = []
    missing: dict[str, str] = {}
    for trial in trials:
        run_id = str(trial.get("run_id", ""))
        by_task: dict[str, Mapping[str, Any]] = {}
        duplicates: set[str] = set()
        observations = trial.get("observations")
        if not isinstance(observations, list):
            observations = []
        for value in observations:
            if not isinstance(value, Mapping):
                continue
            task_id = value.get("task_id")
            if not isinstance(task_id, str):
                continue
            if task_id in by_task:
                duplicates.add(task_id)
            by_task[task_id] = value
        row: list[float] = []
        for task_id in ordered_tasks:
            item = by_task.get(task_id)
            cell_id = f"{run_id}/{task_id}"
            if item is None:
                missing[cell_id] = "missing-observation"
                continue
            if item.get("measurement_status") != "valid":
                missing[cell_id] = "invalid-observation"
                continue
            try:
                row.append(_finite_number(item["normalized_score"], cell_id))
            except (KeyError, ValueError):
                missing[cell_id] = "invalid-normalized-score"
        for task_id in duplicates:
            missing[f"{run_id}/{task_id}"] = "duplicate-observation"
        if len(row) == len(ordered_tasks):
            matrix.append(row)
    if missing or len(matrix) != len(trials):
        base["excluded_ids"] = sorted(missing)
        base["exclusion_reasons"] = dict(sorted(missing.items()))
        base["unavailable_reason"] = "incomplete-rectangular-matrix"
        return base

    original = statistics.fmean(value for row in matrix for value in row)
    seed_hex = str(base["seed_sha256"])
    generator = random.Random(int(seed_hex, 16))
    replicate_values: list[float] = []
    trial_count = len(matrix)
    task_count = len(ordered_tasks)
    for _ in range(RESAMPLING_REPLICATES):
        sampled_trials = [generator.randrange(trial_count) for _ in range(trial_count)]
        sampled_tasks = [generator.randrange(task_count) for _ in range(task_count)]
        per_task = [
            statistics.fmean(matrix[trial_index][task_index] for trial_index in sampled_trials)
            for task_index in sampled_tasks
        ]
        replicate_values.append(statistics.fmean(per_task))
    replicate_values.sort()
    base.update(
        {
            "estimate": original,
            "interval": {
                "level": 0.95,
                "low": _type7_quantile(replicate_values, 0.025),
                "high": _type7_quantile(replicate_values, 0.975),
            },
            "standard_deviation": statistics.stdev(replicate_values),
            "range": {
                "min": replicate_values[0],
                "max": replicate_values[-1],
            },
            "warnings": (
                ["fewer-than-five-trials"] if len(trials) < 5 else []
            ),
        }
    )
    return base


def load_study_summary(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read study summary {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError(f"study summary {path} must be a JSON object")
    study = dict(loaded)
    if study.get("schema_version") == 3:
        return validate_current_study(study)
    trials = study.get("trials")
    if not isinstance(trials, list):
        raise ValueError(f"study summary {path} has no trials list")
    if all(
        isinstance(trial, dict) and isinstance(trial.get("observations"), list)
        for trial in trials
    ):
        study["aggregate_only"] = False
        return study

    task_digests = study.get("metadata", {}).get("corpus_task_digests", {})
    if not isinstance(task_digests, dict):
        task_digests = {}
    results_root = path.parent.parent.parent
    hydrated: list[dict[str, Any]] = []
    for trial_value in trials:
        if not isinstance(trial_value, dict):
            study["aggregate_only"] = True
            return study
        run_id = trial_value.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            study["aggregate_only"] = True
            return study
        run_path = results_root / run_id / "summary.json"
        try:
            run_summary = json.loads(run_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return _aggregate_only(study, "referenced-run-summary-unavailable")
        tasks = run_summary.get("tasks") if isinstance(run_summary, dict) else None
        if not isinstance(tasks, list) or not tasks:
            return _aggregate_only(study, "referenced-run-summary-unavailable")
        try:
            observations = [
                normalize_task_observation(
                    task,
                    task_digest=task_digests.get(task.get("task_id"))
                    if isinstance(task, dict)
                    else None,
                )
                for task in tasks
            ]
        except ValueError:
            return _aggregate_only(study, "historical-task-schema-not-hydratable")
        if any(item.get("measurement_status") != "valid" for item in observations):
            return _aggregate_only(study, "historical-task-schema-not-hydratable")
        if not _hydrated_totals_match(trial_value, observations):
            return _aggregate_only(study, "hydrated-totals-mismatch")
        hydrated.append({**trial_value, "observations": observations})
    study["trials"] = hydrated
    study["aggregate_only"] = False
    return study


def _aggregate_only(study: Mapping[str, Any], reason: str) -> dict[str, Any]:
    result = dict(study)
    result["aggregate_only"] = True
    result["aggregate_only_reason"] = reason
    return result


def _hydrated_totals_match(
    trial: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]
) -> bool:
    derived: dict[str, int | float] = {
        "score": sum(float(item["score"]) for item in observations),
        "max_score": sum(float(item["max_score"]) for item in observations),
        "passed_tasks": sum(item.get("passed") is True for item in observations),
        "failed_tasks": sum(item.get("passed") is not True for item in observations),
        "task_count": len(observations),
        "timeouts": sum(item.get("agent_timeout") is True for item in observations),
    }
    required = ("score", "max_score", "passed_tasks", "timeouts")
    if any(key not in trial for key in required):
        return False
    for key, expected in derived.items():
        if key not in trial:
            continue
        actual = trial[key]
        if isinstance(actual, bool) or not isinstance(actual, (int, float)):
            return False
        if not math.isclose(float(actual), float(expected), rel_tol=1e-9, abs_tol=1e-9):
            return False
    if "score_rate" in trial:
        max_score = float(derived["max_score"])
        expected_rate = float(derived["score"]) / max_score if max_score else 0.0
        actual_rate = trial["score_rate"]
        if (
            isinstance(actual_rate, bool)
            or not isinstance(actual_rate, (int, float))
            or not math.isclose(
                float(actual_rate), expected_rate, rel_tol=1e-9, abs_tol=1e-9
            )
        ):
            return False
    return True


def build_study_report(study: Mapping[str, Any]) -> dict[str, Any]:
    if study.get("schema_version") == 3:
        study = validate_current_study(study)
    trials_value = study.get("trials")
    if not isinstance(trials_value, list):
        raise ValueError("study has no trials list")
    metadata = study.get("metadata")
    if not isinstance(metadata, Mapping):
        metadata = {}
    aggregate_only = study.get("aggregate_only") is True
    if not aggregate_only:
        aggregate_only = any(
            not isinstance(trial, Mapping)
            or not isinstance(trial.get("observations"), list)
            for trial in trials_value
        )
    attempts = _attempt_report(study)
    identity = {
        "study_id": study.get("study_id"),
        "corpus_id": metadata.get("corpus_id"),
        "corpus_digest": metadata.get("corpus_digest"),
        "configuration_id": metadata.get("configuration_id"),
    }
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        **identity,
        "aggregate_only": aggregate_only,
        "attempts": attempts,
        "strata": None,
        "timing": [],
        "combined_timing_interval": None,
        "warnings": [],
    }
    if aggregate_only:
        report["warnings"] = ["task-observations-unavailable"]
        return report

    trials = [dict(trial) for trial in trials_value if isinstance(trial, Mapping)]
    observations: list[tuple[str, Mapping[str, Any]]] = []
    for trial in trials:
        run_id = _nonempty_string(trial.get("run_id"), "trial run_id")
        values = trial.get("observations")
        if not isinstance(values, list):
            raise ValueError(f"trial {run_id} has no observations list")
        task_ids: list[str] = []
        for item in values:
            if not isinstance(item, Mapping):
                raise ValueError(f"trial {run_id} contains a non-object observation")
            if item.get("measurement_status") != "valid":
                raise ValueError(
                    f"publishable trial {run_id} contains an invalid task observation"
                )
            task_id = _nonempty_string(item.get("task_id"), "observation task_id")
            category = _nonempty_string(item.get("category"), f"{task_id}: category")
            _validate_category(category)
            _finite_number(item.get("normalized_score"), f"{run_id}/{task_id}: score")
            task_ids.append(task_id)
            observations.append((run_id, item))
        if len(task_ids) != len(set(task_ids)):
            raise ValueError(f"trial {run_id} contains duplicate task observations")

    if not observations:
        report["strata"] = {
            "whole_corpus": None,
            "categories": {},
            "difficulties": {},
            "tasks": {},
            "criteria": {},
            "failure_classes": {},
        }
        report["warnings"] = ["no-valid-task-observations"]
        return report

    corpus_id = str(metadata.get("corpus_id") or metadata.get("corpus_digest") or "unknown")
    configuration_id = str(metadata.get("configuration_id") or "unknown")
    whole_task_ids = sorted({str(item["task_id"]) for _, item in observations})
    categories = sorted({str(item["category"]) for _, item in observations})
    difficulties = sorted({str(item["difficulty"]) for _, item in observations})
    strata: dict[str, Any] = {
        "whole_corpus": _summarize_stratum(
            "whole-corpus",
            observations,
            trials,
            whole_task_ids,
            attempts,
            corpus_id,
            configuration_id,
        ),
        "categories": {},
        "difficulties": {},
        "tasks": {},
        "criteria": {},
        "failure_classes": {},
    }
    for category in categories:
        selected = [(run_id, item) for run_id, item in observations if item["category"] == category]
        task_ids = sorted({str(item["task_id"]) for _, item in selected})
        strata["categories"][category] = _summarize_stratum(
            f"category:{category}", selected, trials, task_ids, attempts,
            corpus_id, configuration_id, category=category,
        )
    for difficulty in difficulties:
        selected = [(run_id, item) for run_id, item in observations if item["difficulty"] == difficulty]
        task_ids = sorted({str(item["task_id"]) for _, item in selected})
        strata["difficulties"][difficulty] = _summarize_stratum(
            f"difficulty:{difficulty}", selected, trials, task_ids, attempts,
            corpus_id, configuration_id, difficulty=difficulty,
        )
    for task_id in whole_task_ids:
        selected = [(run_id, item) for run_id, item in observations if item["task_id"] == task_id]
        task_summary = _summarize_stratum(
            f"task:{task_id}", selected, trials, [task_id], attempts,
            corpus_id, configuration_id, task_id=task_id,
        )
        task_summary["pass_stability"] = wilson_interval(
            sum(item.get("passed") is True for _, item in selected),
            len(selected),
            included_ids=[f"{run_id}/{task_id}" for run_id, _ in selected],
        )
        strata["tasks"][task_id] = task_summary

    criterion_cells: dict[str, list[tuple[str, Mapping[str, Any], bool]]] = defaultdict(list)
    failure_cells: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
    for run_id, item in observations:
        for criterion in _string_list(item.get("passed_criteria", [])):
            criterion_cells[criterion].append((run_id, item, True))
        for criterion in _string_list(item.get("failed_criteria", [])):
            criterion_cells[criterion].append((run_id, item, False))
        for failure_class in _string_list(item.get("failure_classes", [])):
            failure_cells[failure_class].append((run_id, item))
    for criterion, cells in sorted(criterion_cells.items()):
        numerator = sum(passed for _, _, passed in cells)
        strata["criteria"][criterion] = _frequency_result(
            "criterion-frequency",
            criterion,
            numerator,
            len(cells),
            [f"{run_id}/{item['task_id']}" for run_id, item, _ in cells],
            task_count=len({str(item["task_id"]) for _, item, _ in cells}),
            trial_count=len({run_id for run_id, _, _ in cells}),
            invalid_attempt_count=attempts["invalid_count"] + attempts["incomplete_count"],
            timeout_count=sum(item.get("agent_timeout") is True for _, item, _ in cells),
        )
    for failure_class in sorted(FAILURE_CLASSES):
        cells = failure_cells[failure_class]
        matching = {(run_id, str(item["task_id"])) for run_id, item in cells}
        denominator = len(observations)
        strata["failure_classes"][failure_class] = _frequency_result(
            "failure-class-frequency",
            failure_class,
            len(matching),
            denominator,
            [f"{run_id}/{item['task_id']}" for run_id, item in observations],
            task_count=len(whole_task_ids),
            trial_count=len(trials),
            invalid_attempt_count=attempts["invalid_count"] + attempts["incomplete_count"],
            timeout_count=sum(
                item.get("agent_timeout") is True for _, item in observations
            ),
        )
    report["strata"] = strata
    timing_groups: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for trial in trials:
        environment = str(
            trial.get("timing_environment_id")
            or metadata.get("timing_environment_id")
            or "unknown"
        )
        timing_groups[environment].append(trial)
    report["timing"] = [
        _timing_summary(environment, values)
        for environment, values in sorted(timing_groups.items())
    ]
    if len(report["timing"]) == 1:
        report["combined_timing_interval"] = report["timing"][0]
    elif len(report["timing"]) > 1:
        report["warnings"].append("multiple-timing-environments")
    return report


def build_configuration_report(
    studies: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    if not studies:
        raise ValueError("a configuration report requires at least one study")
    metadata_values = [
        study.get("metadata") if isinstance(study.get("metadata"), Mapping) else {}
        for study in studies
    ]
    corpus_digests = {value.get("corpus_digest") for value in metadata_values}
    configuration_ids = {value.get("configuration_id") for value in metadata_values}
    if len(corpus_digests) != 1 or len(configuration_ids) != 1:
        raise ValueError("configuration reports cannot mix corpus or configuration identities")
    task_counts = {study.get("task_count") for study in studies}
    if len(task_counts) != 1:
        raise ValueError("configuration reports cannot mix task counts")
    trials: list[dict[str, Any]] = []
    excluded_trials: list[dict[str, str]] = []
    attempts: list[dict[str, Any]] = []
    for study, metadata in zip(studies, metadata_values):
        timing_environment = metadata.get("timing_environment_id")
        for value in study.get("trials", []):
            if isinstance(value, Mapping):
                observations = value.get("observations")
                if study.get("aggregate_only") is True or not isinstance(
                    observations, list
                ):
                    excluded_trials.append(
                        {
                            "study_id": str(study.get("study_id") or "unknown"),
                            "run_id": str(value.get("run_id") or "unknown"),
                            "reason": "task-observations-unavailable",
                        }
                    )
                else:
                    trials.append(
                        {
                            **value,
                            "timing_environment_id": timing_environment or "unknown",
                        }
                    )
        for value in study.get("attempts", []):
            if isinstance(value, Mapping):
                attempts.append(dict(value))
    combined = {
        "schema_version": (
            3 if all(study.get("schema_version") == 3 for study in studies) else 2
        ),
        "study_id": "configuration:" + str(next(iter(configuration_ids))),
        "metadata": dict(metadata_values[0]),
        "trial_count": len(trials),
        "task_count": next(iter(task_counts)),
        "trials": trials,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "aggregate_only": not trials,
    }
    report = build_study_report(combined)
    report["excluded_trials"] = excluded_trials
    if excluded_trials and "task-observation-trials-excluded" not in report["warnings"]:
        report["warnings"].append("task-observation-trials-excluded")
    return report


def build_corpus_health_report(
    *,
    corpus_digest: str,
    task_evidence: Sequence[Mapping[str, Any]],
    studies: Sequence[Mapping[str, Any]],
    discrimination_min_observations: int = 20,
    discrimination_min_configurations: int = 2,
) -> dict[str, Any]:
    observed: dict[str, list[tuple[str, str, Mapping[str, Any], Sequence[Mapping[str, Any]]]]] = defaultdict(list)
    invalid_by_task: Counter[str] = Counter()
    expected_task_ids = {
        str(item["task_id"])
        for item in task_evidence
        if isinstance(item, Mapping) and isinstance(item.get("task_id"), str)
    }
    for study in studies:
        metadata = study.get("metadata") if isinstance(study.get("metadata"), Mapping) else {}
        if metadata.get("corpus_digest") not in (None, corpus_digest):
            continue
        configuration_id = str(metadata.get("configuration_id") or "unknown")
        trials = study.get("trials")
        if isinstance(trials, list):
            for trial in trials:
                if not isinstance(trial, Mapping):
                    continue
                values = trial.get("observations")
                if not isinstance(values, list):
                    continue
                usable = [item for item in values if isinstance(item, Mapping)]
                run_id = str(trial.get("run_id") or "unknown")
                for item in usable:
                    task_id = item.get("task_id")
                    if isinstance(task_id, str) and item.get("measurement_status") == "valid":
                        observed[task_id].append((configuration_id, run_id, item, usable))
        attempts = study.get("attempts")
        if isinstance(attempts, list):
            for attempt in attempts:
                if not isinstance(attempt, Mapping) or attempt.get("measurement_status") == "valid":
                    continue
                tasks = attempt.get("tasks")
                if not isinstance(tasks, list):
                    invalid_by_task.update(expected_task_ids)
                    continue
                present_task_ids: set[str] = set()
                for task in tasks:
                    if not isinstance(task, Mapping) or not isinstance(
                        task.get("task_id"), str
                    ):
                        continue
                    task_id = str(task["task_id"])
                    present_task_ids.add(task_id)
                    if task.get("measurement_status") == "invalid":
                        invalid_by_task[task_id] += 1
                invalid_by_task.update(expected_task_ids - present_task_ids)

    tasks_report: dict[str, Any] = {}
    for evidence in sorted(task_evidence, key=lambda item: str(item.get("task_id"))):
        task_id = _nonempty_string(evidence.get("task_id"), "health task_id")
        rows = observed.get(task_id, [])
        successes = sum(item.get("passed") is True for _, _, item, _ in rows)
        timeouts = sum(item.get("agent_timeout") is True for _, _, item, _ in rows)
        durations = [
            _finite_number(value, f"{task_id}: evaluator duration")
            for value in evidence.get("evaluator_durations_seconds", [])
        ]
        rows_by_configuration: dict[str, list[tuple[str, Mapping[str, Any]]]] = defaultdict(list)
        for configuration, run_id, item, _ in rows:
            rows_by_configuration[configuration].append((run_id, item))
        pass_stability_by_configuration = {
            configuration: wilson_interval(
                sum(item.get("passed") is True for _, item in values),
                len(values),
                included_ids=[run_id for run_id, _ in values],
            )
            for configuration, values in sorted(rows_by_configuration.items())
        }
        pooled_empirical_pass_rate = {
            "sampling_unit": "valid-task-observation",
            "successes": successes,
            "n": len(rows),
            "estimate": successes / len(rows) if rows else None,
            "configuration_count": len(rows_by_configuration),
            "interval": None,
            "warnings": ["pooled-descriptive-rate-not-per-configuration-stability"],
        }
        discrimination = _task_discrimination(
            task_id,
            rows,
            minimum_observations=discrimination_min_observations,
            minimum_configurations=discrimination_min_configurations,
        )
        solve_rate = successes / len(rows) if rows else None
        criterion_ids = sorted(_string_list(evidence.get("criterion_ids", [])))
        covered = sorted(_string_list(evidence.get("criterion_coverage", [])))
        tasks_report[task_id] = {
            "reference_full_score": evidence.get("reference_full_score") is True,
            "starter_rejected": evidence.get("starter_rejected") is True,
            "pass_fixture_count": int(evidence.get("pass_fixture_count", 0)),
            "reject_fixture_count": int(evidence.get("reject_fixture_count", 0)),
            "criterion_ids": criterion_ids,
            "criterion_coverage": covered,
            "missing_criterion_coverage": sorted(set(criterion_ids) - set(covered)),
            "evaluator_deterministic": evidence.get("evaluator_deterministic") is True,
            "contract_outcomes_match": evidence.get("contract_outcomes_match") is not False,
            "evaluator_runtime_seconds": {
                "n": len(durations),
                "median": statistics.median(durations) if durations else None,
                "max": max(durations) if durations else None,
            },
            "observed_valid_count": len(rows),
            "observed_pass_rate": solve_rate,
            "observed_timeout_rate": timeouts / len(rows) if rows else None,
            "invalid_measurement_count": invalid_by_task[task_id],
            "invalid_measurement_rate": (
                invalid_by_task[task_id] / (len(rows) + invalid_by_task[task_id])
                if len(rows) + invalid_by_task[task_id]
                else None
            ),
            "pass_stability_by_configuration": pass_stability_by_configuration,
            "pooled_empirical_pass_rate": pooled_empirical_pass_rate,
            "discrimination": discrimination,
            "author_difficulty": evidence.get("difficulty"),
            "empirical_solve_rate_band": _solve_rate_band(solve_rate),
            "category": evidence.get("category"),
        }
    return {
        "schema_version": CORPUS_HEALTH_SCHEMA_VERSION,
        "corpus_digest": corpus_digest,
        "discrimination_thresholds": {
            "minimum_observations": discrimination_min_observations,
            "minimum_configurations": discrimination_min_configurations,
        },
        "tasks": tasks_report,
    }


def _summarize_stratum(
    stratum_id: str,
    observations: Sequence[tuple[str, Mapping[str, Any]]],
    trials: Sequence[Mapping[str, Any]],
    task_ids: Sequence[str],
    attempts: Mapping[str, Any],
    corpus_id: str,
    configuration_id: str,
    *,
    category: str | None = None,
    difficulty: str | None = None,
    task_id: str | None = None,
) -> dict[str, Any]:
    by_task: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    by_run: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for run_id, item in observations:
        by_task[str(item["task_id"])].append(item)
        by_run[run_id].append(item)
    macro_task_score = statistics.fmean(
        statistics.fmean(float(item["normalized_score"]) for item in values)
        for values in by_task.values()
    )
    macro_pass_rate = statistics.fmean(
        statistics.fmean(1.0 if item.get("passed") is True else 0.0 for item in values)
        for values in by_task.values()
    )
    earned = sum(float(item["score"]) for _, item in observations)
    available = sum(float(item["max_score"]) for _, item in observations)
    timeout_count = sum(item.get("agent_timeout") is True for _, item in observations)
    expected_tasks = set(task_ids)
    trial_rates: list[float] = []
    included_runs: list[str] = []
    excluded_runs: dict[str, str] = {}
    for trial in trials:
        run_id = str(trial["run_id"])
        values = by_run.get(run_id, [])
        actual_tasks = {str(item["task_id"]) for item in values}
        if actual_tasks != expected_tasks:
            excluded_runs[run_id] = "incomplete-task-row"
            continue
        included_runs.append(run_id)
        trial_rates.append(
            statistics.fmean(float(item["normalized_score"]) for item in values)
        )
    selected_trials = []
    for trial in trials:
        values = trial.get("observations")
        if not isinstance(values, list):
            continue
        filtered = [
            item
            for item in values
            if isinstance(item, Mapping)
            and str(item.get("task_id")) in set(task_ids)
        ]
        selected_trials.append({**trial, "observations": filtered})
    task_count = len(set(task_ids))
    descriptive_only = task_count < 5
    if task_id is not None:
        invalid_attempt_count = int(attempts["by_task"].get(task_id, 0))
    elif category is not None:
        invalid_attempt_count = int(attempts["by_category"].get(category, 0))
    elif difficulty is not None:
        invalid_attempt_count = int(attempts["by_difficulty"].get(difficulty, 0))
    else:
        invalid_attempt_count = attempts["invalid_count"] + attempts["incomplete_count"]
    return {
        "id": stratum_id,
        "category": category,
        "difficulty": difficulty,
        "task_id": task_id,
        "task_count": task_count,
        "valid_observation_count": len(observations),
        "invalid_attempt_count": invalid_attempt_count,
        "trial_count": len(by_run),
        "complete_trial_count": len(included_runs),
        "mean_normalized_score": macro_task_score,
        "macro_task_score": macro_task_score,
        "macro_pass_rate": macro_pass_rate,
        "pass_rate": macro_pass_rate,
        "point_weighted_score": earned / available if available else None,
        "raw_points": {"earned": earned, "available": available},
        "timeout_count": timeout_count,
        "timeout_rate": timeout_count / len(observations),
        "normalized_score_range": {
            "min": min(float(item["normalized_score"]) for _, item in observations),
            "max": max(float(item["normalized_score"]) for _, item in observations),
        },
        "descriptive_only": descriptive_only,
        "status": "descriptive" if descriptive_only else "estimable",
        "run_variation": (
            fixed_corpus_interval(
                trial_rates,
                included_ids=included_runs,
                excluded_reasons=excluded_runs,
                display_bounds=(0.0, 1.0),
            )
            if trial_rates
            else _unavailable_run_variation(excluded_runs)
        ),
        "resampling_sensitivity": resampling_sensitivity(
            selected_trials,
            task_ids=task_ids,
            corpus_id=corpus_id,
            configuration_id=configuration_id,
            stratum_id=stratum_id,
        ),
    }


def _attempt_report(study: Mapping[str, Any]) -> dict[str, Any]:
    trials = study.get("trials") if isinstance(study.get("trials"), list) else []
    attempts_value = study.get("attempts")
    attempts = attempts_value if isinstance(attempts_value, list) else []
    if not attempts:
        attempts = [
            {
                "run_id": trial.get("run_id"),
                "measurement_status": "valid",
                "exclusion_reasons": [],
            }
            for trial in trials
            if isinstance(trial, Mapping)
        ]
    invalid = [item for item in attempts if isinstance(item, Mapping) and item.get("measurement_status") == "invalid"]
    incomplete = [item for item in attempts if isinstance(item, Mapping) and item.get("measurement_status") == "incomplete"]
    reasons: Counter[str] = Counter()
    by_task: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    by_difficulty: Counter[str] = Counter()
    expected: dict[str, tuple[str | None, str | None]] = {}
    for trial in trials:
        if not isinstance(trial, Mapping) or not isinstance(
            trial.get("observations"), list
        ):
            continue
        for task in trial["observations"]:
            if not isinstance(task, Mapping) or not isinstance(task.get("task_id"), str):
                continue
            expected[str(task["task_id"])] = (
                str(task["category"]) if isinstance(task.get("category"), str) else None,
                str(task["difficulty"])
                if isinstance(task.get("difficulty"), str)
                else None,
            )
    for item in [*invalid, *incomplete]:
        reasons.update(_string_list(item.get("exclusion_reasons", [])))
        tasks = item.get("tasks")
        if not isinstance(tasks, list):
            by_task.update(expected.keys())
            by_category.update(
                category for category, _ in expected.values() if category is not None
            )
            by_difficulty.update(
                difficulty
                for _, difficulty in expected.values()
                if difficulty is not None
            )
            continue
        present_task_ids: set[str] = set()
        invalid_task_ids: set[str] = set()
        attempt_metadata: dict[str, tuple[str | None, str | None]] = {}
        for task in tasks:
            if not isinstance(task, Mapping):
                continue
            if isinstance(task.get("task_id"), str):
                task_id = str(task["task_id"])
                present_task_ids.add(task_id)
                attempt_metadata[task_id] = (
                    str(task["category"])
                    if isinstance(task.get("category"), str)
                    else None,
                    str(task["difficulty"])
                    if isinstance(task.get("difficulty"), str)
                    else None,
                )
                if task.get("measurement_status") == "invalid":
                    invalid_task_ids.add(task_id)
        affected_task_ids = invalid_task_ids | (set(expected) - present_task_ids)
        by_task.update(affected_task_ids)
        by_category.update(
            category
            for task_id in affected_task_ids
            for category, _ in [
                expected.get(task_id, attempt_metadata.get(task_id, (None, None)))
            ]
            if category is not None
        )
        by_difficulty.update(
            difficulty
            for task_id in affected_task_ids
            for _, difficulty in [
                expected.get(task_id, attempt_metadata.get(task_id, (None, None)))
            ]
            if difficulty is not None
        )
    return {
        "total_count": len(attempts),
        "valid_count": len(attempts) - len(invalid) - len(incomplete),
        "invalid_count": len(invalid),
        "incomplete_count": len(incomplete),
        "invalid_rate": len(invalid) / len(attempts) if attempts else 0.0,
        "excluded_rate": (len(invalid) + len(incomplete)) / len(attempts) if attempts else 0.0,
        "reasons": dict(sorted(reasons.items())),
        "by_task": dict(sorted(by_task.items())),
        "by_category": dict(sorted(by_category.items())),
        "by_difficulty": dict(sorted(by_difficulty.items())),
    }


def _unavailable_run_variation(
    excluded_reasons: Mapping[str, str],
) -> dict[str, Any]:
    return {
        "method": "student-t-fixed-corpus-run-variation",
        "method_version": FIXED_CORPUS_METHOD_VERSION,
        "sampling_unit": "complete-corpus-trial",
        "n": 0,
        "included_ids": [],
        "excluded_ids": sorted(excluded_reasons),
        "exclusion_reasons": dict(sorted(excluded_reasons.items())),
        "estimate": None,
        "interval": None,
        "standard_deviation": None,
        "range": None,
        "warnings": ["no-complete-trials"],
        "unavailable_reason": "incomplete-task-matrix",
    }


def _timing_summary(
    timing_environment_id: str, trials: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    run_ids: list[str] = []
    agent_times: list[float] = []
    evaluator_times: list[float] = []
    for trial in trials:
        run_id = _nonempty_string(trial.get("run_id"), "timing trial run_id")
        values = trial.get("observations")
        if not isinstance(values, list):
            continue
        observations = [item for item in values if isinstance(item, Mapping)]
        run_ids.append(run_id)
        agent_times.append(
            sum(float(item["agent_duration_seconds"]) for item in observations)
        )
        evaluator_times.append(
            sum(float(item["evaluator_duration_seconds"]) for item in observations)
        )
    return {
        "timing_environment_id": timing_environment_id,
        "trial_count": len(run_ids),
        "agent_time_seconds": fixed_corpus_interval(
            agent_times, included_ids=run_ids, display_bounds=(0.0, None)
        ),
        "evaluator_time_seconds": fixed_corpus_interval(
            evaluator_times, included_ids=run_ids, display_bounds=(0.0, None)
        ),
    }


def _frequency_result(
    method: str,
    key: str,
    numerator: int,
    denominator: int,
    included_ids: Sequence[str],
    *,
    task_count: int,
    trial_count: int,
    invalid_attempt_count: int,
    timeout_count: int,
) -> dict[str, Any]:
    return {
        "method": method,
        "method_version": "1",
        "sampling_unit": "valid-task-observation",
        "id": key,
        "n": denominator,
        "included_ids": list(included_ids),
        "excluded_ids": [],
        "exclusion_reasons": {},
        "numerator": numerator,
        "denominator": denominator,
        "estimate": numerator / denominator if denominator else None,
        "interval": None,
        "standard_deviation": None,
        "range": {"min": 0, "max": 1},
        "warnings": ["frequency-only-no-interval"],
        "task_count": task_count,
        "valid_observation_count": denominator,
        "invalid_attempt_count": invalid_attempt_count,
        "timeout_count": timeout_count,
        "timeout_rate": timeout_count / denominator if denominator else None,
        "trial_count": trial_count,
        "mean_normalized_score": None,
        "pass_rate": None,
        "descriptive_only": task_count < 5,
        "status": "descriptive",
    }


def _task_discrimination(
    task_id: str,
    rows: Sequence[tuple[str, str, Mapping[str, Any], Sequence[Mapping[str, Any]]]],
    *,
    minimum_observations: int,
    minimum_configurations: int,
) -> dict[str, Any]:
    base = {
        "method": "point-biserial-leave-one-task-out",
        "method_version": "1",
        "sampling_unit": "valid-task-observation",
        "n": 0,
        "configuration_count": 0,
        "estimate": None,
        "unavailable_reason": None,
        "leave_one_task_out_statistic": "sum-normalized-task-scores",
    }
    outcomes: list[float] = []
    other_scores: list[float] = []
    included_configurations: list[str] = []
    for configuration, _, item, all_items in rows:
        other = [
            float(value["normalized_score"])
            for value in all_items
            if value.get("task_id") != task_id
            and value.get("measurement_status") == "valid"
        ]
        if not other:
            continue
        outcomes.append(1.0 if item.get("passed") is True else 0.0)
        other_scores.append(sum(other))
        included_configurations.append(configuration)
    configurations = set(included_configurations)
    base["n"] = len(outcomes)
    base["configuration_count"] = len(configurations)
    if len(outcomes) < minimum_observations:
        base["unavailable_reason"] = "insufficient-sample-size"
        return base
    if len(configurations) < minimum_configurations:
        base["unavailable_reason"] = "insufficient-configuration-diversity"
        return base
    if len(set(outcomes)) < 2 or len(set(other_scores)) < 2:
        base["unavailable_reason"] = "zero-variance"
        return base
    base["estimate"] = statistics.correlation(outcomes, other_scores)
    return base


def _solve_rate_band(rate: float | None) -> str | None:
    if rate is None:
        return None
    if rate < 0.25:
        return "low"
    if rate < 0.75:
        return "mixed"
    return "high"


def _resampling_seed(corpus_id: str, configuration_id: str, stratum_id: str) -> str:
    material = "\0".join(
        [corpus_id, configuration_id, stratum_id, RESAMPLING_METHOD_VERSION]
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _t_critical_95(degrees_of_freedom: int) -> float:
    if degrees_of_freedom < 1:
        raise ValueError("degrees_of_freedom must be positive")
    if degrees_of_freedom in T_CRITICAL_95:
        return T_CRITICAL_95[degrees_of_freedom]
    z = 1.959963984540054
    df = float(degrees_of_freedom)
    return (
        z
        + (z**3 + z) / (4 * df)
        + (5 * z**5 + 16 * z**3 + 3 * z) / (96 * df**2)
        + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / (384 * df**3)
    )


def _type7_quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot take a quantile of an empty sample")
    if probability < 0 or probability > 1:
        raise ValueError("quantile probability must be within [0, 1]")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    fraction = position - lower
    return float(sorted_values[lower]) + fraction * (
        float(sorted_values[upper]) - float(sorted_values[lower])
    )


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number")
    return number


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ValueError("expected a list of strings")
    return list(value)


def _validate_category(category: str) -> None:
    if category not in VALID_CATEGORIES:
        choices = ", ".join(sorted(VALID_CATEGORIES))
        raise ValueError(f"unknown task category {category!r}; expected one of: {choices}")
