from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from .protocol import (
    CONTROLLED_PROTOCOL_IDENTITY_SCHEMA_VERSION,
    PROTOCOL_FIELDS,
    compute_configuration_id,
)
from .scoring import FAILURE_CLASSES
from .task import VALID_CATEGORIES, VALID_DIFFICULTIES


FLOAT_TOLERANCE = 1e-12
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_CONTROLLED_PROTOCOL_FIELDS = set(PROTOCOL_FIELDS) | {
    "wrapper_prompt_sha256",
    "agent_command_sha256",
    "agent_adapter_sha256",
    "agent_adapter_bundle_sha256",
    "attestation_trust",
}


class StudyValidationError(ValueError):
    """A current study disagrees with its primitive task evidence."""


def normalize_task_observation(
    task: Mapping[str, Any], *, task_digest: object = None
) -> dict[str, Any]:
    """Normalize writer-side task evidence without trusting redundant totals."""
    task_id = _nonempty_string(task.get("task_id"), "task_id")
    category = _controlled_string(
        task.get("category"), VALID_CATEGORIES, f"{task_id}: category"
    )
    difficulty = _controlled_string(
        task.get("difficulty"), VALID_DIFFICULTIES, f"{task_id}: difficulty"
    )
    measurement_status = _nonempty_string(
        task.get("measurement_status"), f"{task_id}: measurement_status"
    )
    score = _finite_number(task.get("score"), f"{task_id}: score")
    max_score = _finite_number(task.get("max_score"), f"{task_id}: max_score")
    if max_score <= 0 or score < 0 or score > max_score:
        raise StudyValidationError(f"{task_id}: score must be within max_score")
    criteria = task.get("criteria", {})
    if not isinstance(criteria, Mapping) or not all(
        isinstance(key, str) and key and type(value) is bool
        for key, value in criteria.items()
    ):
        raise StudyValidationError(
            f"{task_id}: criteria must contain boolean outcomes"
        )

    score_detail = task.get("score_detail")
    detail = score_detail if isinstance(score_detail, Mapping) else {}
    criterion_points = _number_map(detail.get("criterion_points"), allow_empty=True)
    criterion_failure_classes = _string_map(
        detail.get("criterion_failure_classes"), allow_empty=True
    )
    required_criteria = _string_list(detail.get("required_criteria", []))

    agent = task.get("agent")
    check = task.get("check")
    agent_duration = 0.0
    agent_timeout = False
    if isinstance(agent, Mapping):
        agent_duration = _finite_number(
            agent.get("duration_seconds", 0), f"{task_id}: agent duration"
        )
        agent_timeout = agent.get("timed_out") is True
    evaluator_duration = 0.0
    if isinstance(check, Mapping):
        evaluator_duration = _finite_number(
            check.get("duration_seconds", 0), f"{task_id}: evaluator duration"
        )
    if agent_duration < 0 or evaluator_duration < 0:
        raise StudyValidationError(f"{task_id}: durations must be non-negative")

    passed = task.get("passed") is True
    return {
        "task_id": task_id,
        "task_digest": task_digest if isinstance(task_digest, str) else None,
        "category": category,
        "difficulty": difficulty,
        "measurement_status": measurement_status,
        "task_outcome": task.get("task_outcome"),
        "invalid_reason": task.get("invalid_reason"),
        "scoring_schema": task.get("scoring_schema"),
        "passed": passed,
        "score": score,
        "max_score": max_score,
        "normalized_score": score / max_score,
        "criteria": dict(criteria),
        "criterion_points": criterion_points,
        "criterion_failure_classes": criterion_failure_classes,
        "required_criteria": sorted(required_criteria),
        "passed_criteria": sorted(key for key, value in criteria.items() if value),
        "failed_criteria": sorted(key for key, value in criteria.items() if not value),
        "failure_classes": sorted(_string_list(task.get("failure_classes", []))),
        "agent_duration_seconds": agent_duration,
        "evaluator_duration_seconds": evaluator_duration,
        "agent_timeout": agent_timeout,
        "infrastructure_events": sorted(
            _string_list(task.get("infrastructure_events", []))
        ),
    }


def validate_current_study(study: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return a normalized schema-3 study.

    Schema versions before 3 are intentionally outside this validator and remain
    on the reporting module's explicit legacy/aggregate-only path.
    """
    if study.get("schema_version") != 3:
        raise StudyValidationError("current study schema_version must be 3")
    metadata_value = study.get("metadata")
    if not isinstance(metadata_value, Mapping):
        raise StudyValidationError("current study metadata is missing")
    metadata = dict(metadata_value)
    corpus_digest = _sha256(metadata.get("corpus_digest"), "corpus_digest")
    controlled_version = metadata.get("controlled_protocol_schema_version")
    if controlled_version != CONTROLLED_PROTOCOL_IDENTITY_SCHEMA_VERSION:
        raise StudyValidationError(
            "current study is missing canonical controlled protocol payload"
        )
    controlled_value = metadata.get("controlled_protocol")
    if not isinstance(controlled_value, Mapping):
        raise StudyValidationError(
            "current study is missing canonical controlled protocol payload"
        )
    controlled = dict(controlled_value)
    if set(controlled) != _CONTROLLED_PROTOCOL_FIELDS:
        raise StudyValidationError(
            "current study controlled protocol fields are incomplete or unknown"
        )
    configuration_id = _nonempty_string(
        metadata.get("configuration_id"), "configuration_id"
    )
    expected_configuration_id = compute_configuration_id(corpus_digest, controlled)
    if configuration_id != expected_configuration_id:
        raise StudyValidationError(
            "configuration_id does not match controlled protocol"
        )
    _validate_flattened_protocol_metadata(metadata, controlled)

    trials_value = study.get("trials")
    if not isinstance(trials_value, list):
        raise StudyValidationError("current study has no trials list")
    normalized_trials: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    cells: set[tuple[str, str]] = set()
    expected_task_set: set[str] | None = None
    for trial_value in trials_value:
        if not isinstance(trial_value, Mapping):
            raise StudyValidationError("current study trial is not an object")
        trial = _validate_trial(
            trial_value,
            corpus_digest=corpus_digest,
            configuration_id=configuration_id,
        )
        run_id = str(trial["run_id"])
        if run_id in run_ids:
            raise StudyValidationError("duplicate trial run_id")
        run_ids.add(run_id)
        task_set = {str(item["task_id"]) for item in trial["observations"]}
        if expected_task_set is None:
            expected_task_set = task_set
        elif task_set != expected_task_set:
            raise StudyValidationError("study trials do not contain the same task matrix")
        for task_id in task_set:
            cell = (run_id, task_id)
            if cell in cells:
                raise StudyValidationError("duplicate study task cell")
            cells.add(cell)
        normalized_trials.append(trial)

    declared_trial_count = study.get("trial_count")
    if type(declared_trial_count) is not int or declared_trial_count != len(normalized_trials):
        raise StudyValidationError("study trial_count disagrees with trials")
    declared_task_count = study.get("task_count")
    derived_task_count = len(expected_task_set or ())
    if type(declared_task_count) is not int or declared_task_count <= 0:
        raise StudyValidationError("study task_count must be a positive integer")
    if normalized_trials and declared_task_count != derived_task_count:
        raise StudyValidationError("study task_count disagrees with observations")

    return {
        **dict(study),
        "metadata": metadata,
        "trials": normalized_trials,
        "aggregate_only": False,
    }


def _validate_trial(
    trial: Mapping[str, Any], *, corpus_digest: str, configuration_id: str
) -> dict[str, Any]:
    run_id = _nonempty_string(trial.get("run_id"), "trial run_id")
    if trial.get("measurement_status") != "valid":
        raise StudyValidationError(f"trial {run_id} measurement_status is not valid")
    if trial.get("scoring_schema") != "criteria-v2":
        raise StudyValidationError(f"trial {run_id} scoring_schema is not criteria-v2")
    if trial.get("corpus_digest") != corpus_digest:
        raise StudyValidationError(f"trial {run_id} corpus_digest disagrees with metadata")
    if trial.get("configuration_id") != configuration_id:
        raise StudyValidationError(
            f"trial {run_id} configuration_id disagrees with metadata"
        )
    observations_value = trial.get("observations")
    if not isinstance(observations_value, list) or not observations_value:
        raise StudyValidationError(f"trial {run_id} has no observations")
    observations: list[dict[str, Any]] = []
    task_ids: set[str] = set()
    for value in observations_value:
        if not isinstance(value, Mapping):
            raise StudyValidationError(f"trial {run_id} contains a non-object observation")
        observation = _validate_observation(value, run_id=run_id)
        task_id = str(observation["task_id"])
        if task_id in task_ids:
            raise StudyValidationError(f"trial {run_id} contains duplicate task cells")
        task_ids.add(task_id)
        observations.append(observation)

    derived = _derive_trial_aggregates(observations)
    for field, expected in derived.items():
        actual = trial.get(field)
        if not _values_equal(actual, expected):
            raise StudyValidationError(f"trial {run_id} aggregate {field} disagrees with observations")
    return {**dict(trial), **derived, "observations": observations}


def _validate_observation(value: Mapping[str, Any], *, run_id: str) -> dict[str, Any]:
    task_id = _nonempty_string(value.get("task_id"), f"{run_id}: task_id")
    label = f"{run_id}/{task_id}"
    task_digest = _sha256(value.get("task_digest"), f"{label}: task_digest")
    category = _controlled_string(value.get("category"), VALID_CATEGORIES, f"{label}: category")
    difficulty = _controlled_string(
        value.get("difficulty"), VALID_DIFFICULTIES, f"{label}: difficulty"
    )
    if value.get("measurement_status") != "valid":
        raise StudyValidationError(f"{label}: measurement_status must be valid")
    if value.get("invalid_reason") is not None:
        raise StudyValidationError(f"{label}: valid observation has invalid_reason")
    if value.get("scoring_schema") != "criteria-v2":
        raise StudyValidationError(f"{label}: scoring_schema must be criteria-v2")
    score = _finite_number(value.get("score"), f"{label}: score")
    max_score = _finite_number(value.get("max_score"), f"{label}: max_score")
    if max_score <= 0 or score < 0 or score > max_score:
        raise StudyValidationError(f"{label}: score must be within max_score")
    normalized_score = _finite_number(
        value.get("normalized_score"), f"{label}: normalized_score"
    )
    if not math.isclose(
        normalized_score, score / max_score, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE
    ):
        raise StudyValidationError(f"{label}: normalized_score disagrees with score/max_score")

    criteria_value = value.get("criteria")
    if not isinstance(criteria_value, Mapping) or not criteria_value or not all(
        isinstance(key, str) and key and type(outcome) is bool
        for key, outcome in criteria_value.items()
    ):
        raise StudyValidationError(f"{label}: criteria must contain boolean outcomes")
    criteria = dict(criteria_value)
    criterion_ids = set(criteria)
    points = _number_map(value.get("criterion_points"))
    classes = _string_map(value.get("criterion_failure_classes"))
    required = _string_list(value.get("required_criteria"))
    if set(points) != criterion_ids or set(classes) != criterion_ids:
        raise StudyValidationError(f"{label}: scoring rubric does not match criteria")
    if (
        not required
        or len(required) != len(set(required))
        or not set(required) <= criterion_ids
    ):
        raise StudyValidationError(f"{label}: required criteria are invalid")
    if any(point <= 0 for point in points.values()) or not math.isclose(
        sum(points.values()), max_score, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE
    ):
        raise StudyValidationError(f"{label}: criterion points disagree with max_score")
    if any(failure_class not in FAILURE_CLASSES for failure_class in classes.values()):
        raise StudyValidationError(f"{label}: criterion failure class is invalid")
    expected_score = sum(points[key] for key, outcome in criteria.items() if outcome)
    if not math.isclose(score, expected_score, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE):
        raise StudyValidationError(f"{label}: score disagrees with criteria")

    agent_timeout = value.get("agent_timeout")
    if type(agent_timeout) is not bool:
        raise StudyValidationError(f"{label}: agent_timeout must be boolean")
    expected_passed = (
        not agent_timeout and all(criteria[key] for key in required)
    )
    passed = value.get("passed")
    if type(passed) is not bool or passed != expected_passed:
        raise StudyValidationError(f"{label}: passed disagrees with required criteria")
    expected_passed_criteria = sorted(key for key, outcome in criteria.items() if outcome)
    expected_failed_criteria = sorted(key for key, outcome in criteria.items() if not outcome)
    if _string_list(value.get("passed_criteria")) != expected_passed_criteria:
        raise StudyValidationError(f"{label}: passed_criteria disagrees with criteria")
    if _string_list(value.get("failed_criteria")) != expected_failed_criteria:
        raise StudyValidationError(f"{label}: failed_criteria disagrees with criteria")
    expected_failure_classes = sorted({classes[key] for key in expected_failed_criteria})
    if _string_list(value.get("failure_classes")) != expected_failure_classes:
        raise StudyValidationError(f"{label}: failure_classes disagree with criteria")

    expected_outcome = "agent-timeout" if agent_timeout else ("pass" if passed else "fail")
    if value.get("task_outcome") != expected_outcome:
        raise StudyValidationError(f"{label}: task_outcome disagrees with timeout/pass state")
    agent_duration = _finite_number(
        value.get("agent_duration_seconds"), f"{label}: agent_duration_seconds"
    )
    evaluator_duration = _finite_number(
        value.get("evaluator_duration_seconds"), f"{label}: evaluator_duration_seconds"
    )
    if agent_duration < 0 or evaluator_duration < 0:
        raise StudyValidationError(f"{label}: durations must be non-negative")
    infrastructure_events = sorted(_string_list(value.get("infrastructure_events")))

    return {
        **dict(value),
        "task_id": task_id,
        "task_digest": task_digest,
        "category": category,
        "difficulty": difficulty,
        "score": score,
        "max_score": max_score,
        "normalized_score": score / max_score,
        "criteria": criteria,
        "criterion_points": points,
        "criterion_failure_classes": classes,
        "required_criteria": sorted(required),
        "passed_criteria": expected_passed_criteria,
        "failed_criteria": expected_failed_criteria,
        "failure_classes": expected_failure_classes,
        "agent_duration_seconds": agent_duration,
        "evaluator_duration_seconds": evaluator_duration,
        "infrastructure_events": infrastructure_events,
    }


def _derive_trial_aggregates(
    observations: Sequence[Mapping[str, Any]],
) -> dict[str, int | float | str]:
    task_count = len(observations)
    score = sum(float(item["score"]) for item in observations)
    max_score = sum(float(item["max_score"]) for item in observations)
    agent_time = sum(float(item["agent_duration_seconds"]) for item in observations)
    return {
        "measurement_status": "valid",
        "passed_tasks": sum(item["passed"] is True for item in observations),
        "failed_tasks": sum(item["passed"] is False for item in observations),
        "task_count": task_count,
        "score": score,
        "max_score": max_score,
        "score_rate": score / max_score,
        "agent_time_seconds": agent_time,
        "agent_seconds_per_task": agent_time / task_count,
        "timeouts": sum(item["agent_timeout"] is True for item in observations),
        "scoring_schema": "criteria-v2",
    }


def _validate_flattened_protocol_metadata(
    metadata: Mapping[str, Any], controlled: Mapping[str, Any]
) -> None:
    flattened = {
        "protocol_id": "id",
        "protocol_schema_version": "schema_version",
        "model_identity_evidence": "model_identity_evidence",
        "completion_attestation": "completion_attestation",
        "agent_adapter": "agent_adapter",
        "agent_adapter_sha256": "agent_adapter_sha256",
        "agent_adapter_bundle_sha256": "agent_adapter_bundle_sha256",
        "attestation_trust": "attestation_trust",
        "wrapper_prompt_sha256": "wrapper_prompt_sha256",
        "agent_command_sha256": "agent_command_sha256",
        "isolation_profile": "isolation_profile",
        "system": "system",
        "agent_timeout_seconds": "agent_timeout_seconds",
    }
    for metadata_field, controlled_field in flattened.items():
        if metadata.get(metadata_field) != controlled.get(controlled_field):
            raise StudyValidationError(
                f"study metadata {metadata_field} disagrees with controlled protocol"
            )


def _values_equal(actual: object, expected: object) -> bool:
    if isinstance(expected, float):
        return (
            not isinstance(actual, bool)
            and isinstance(actual, (int, float))
            and math.isfinite(float(actual))
            and math.isclose(
                float(actual), expected, rel_tol=FLOAT_TOLERANCE, abs_tol=FLOAT_TOLERANCE
            )
        )
    return actual == expected


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StudyValidationError(f"{label} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise StudyValidationError(f"{label} must be a finite number")
    return result


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StudyValidationError(f"{label} must be a non-empty string")
    return value


def _sha256(value: object, label: str) -> str:
    text = _nonempty_string(value, label)
    if _SHA256_PATTERN.fullmatch(text) is None:
        raise StudyValidationError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _controlled_string(value: object, choices: set[str], label: str) -> str:
    text = _nonempty_string(value, label)
    if text not in choices:
        raise StudyValidationError(f"{label} is not in the controlled vocabulary")
    return text


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise StudyValidationError("expected a list of non-empty strings")
    return list(value)


def _number_map(value: object, *, allow_empty: bool = False) -> dict[str, float]:
    if allow_empty and value is None:
        return {}
    if not isinstance(value, Mapping) or (not value and not allow_empty):
        raise StudyValidationError("expected a non-empty numeric object")
    result: dict[str, float] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            raise StudyValidationError("numeric object keys must be non-empty strings")
        result[key] = _finite_number(item, key)
    return result


def _string_map(value: object, *, allow_empty: bool = False) -> dict[str, str]:
    if allow_empty and value is None:
        return {}
    if not isinstance(value, Mapping) or (not value and not allow_empty):
        raise StudyValidationError("expected a non-empty string object")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not key or not isinstance(item, str) or not item:
            raise StudyValidationError("string object entries must be non-empty strings")
        result[key] = item
    return result
