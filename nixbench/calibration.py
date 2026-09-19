from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .corpus import CorpusIdentity
from .reporting import build_corpus_health_report
from .study_validation import validate_current_study
from .task import Task

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


LIFECYCLE_SCHEMA_VERSION = 2
CALIBRATION_SCHEMA_VERSION = 1
CALIBRATION_REPORT_SCHEMA_VERSION = 1
MINIMUM_CALIBRATION_CONFIGURATIONS = 3
MINIMUM_VALID_OBSERVATIONS_PER_CONFIGURATION = 1
LIFECYCLE_STATES = {
    "draft",
    "calibrating",
    "active",
    "quarantined",
    "deprecated",
    "retired",
}
REVIEW_DECISIONS = {"pending", "approve", "quarantine", "reject"}
REVIEW_STATUSES = {"pending", "reviewed-no-issue", "reviewed-issue-resolved", "reviewed-blocking"}


@dataclass(frozen=True)
class LifecycleRegistry:
    states: dict[str, str]

    def task_ids(self, state: str) -> set[str]:
        return {task_id for task_id, value in self.states.items() if value == state}


@dataclass(frozen=True)
class CalibrationRegistry:
    records: dict[str, dict[str, Any]]


def load_lifecycle_registry(path: Path, *, expected_task_ids: Sequence[str]) -> LifecycleRegistry:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read task lifecycle registry {path}: {exc}") from exc
    if set(data) != {"schema_version", "tasks"} or data.get("schema_version") != LIFECYCLE_SCHEMA_VERSION:
        raise ValueError(f"task lifecycle must use schema {LIFECYCLE_SCHEMA_VERSION}")
    values = data.get("tasks")
    if not isinstance(values, list):
        raise ValueError("task lifecycle tasks must be an array")
    states: dict[str, str] = {}
    for value in values:
        if not isinstance(value, Mapping) or set(value) != {"task_id", "state"}:
            raise ValueError("task lifecycle entry fields are invalid")
        task_id = _nonempty_string(value.get("task_id"), "lifecycle task_id")
        state = _nonempty_string(value.get("state"), f"{task_id}: lifecycle state")
        if state not in LIFECYCLE_STATES:
            raise ValueError(f"{task_id}: unknown lifecycle state {state}")
        if task_id in states:
            raise ValueError(f"duplicate lifecycle task {task_id}")
        states[task_id] = state
    expected = set(expected_task_ids)
    if set(states) != expected:
        raise ValueError("task lifecycle entries do not match the corpus task set")
    return LifecycleRegistry(states=states)


def load_calibration_registry(path: Path, *, identity: CorpusIdentity) -> CalibrationRegistry:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read calibration registry {path}: {exc}") from exc
    if not isinstance(value, Mapping):
        raise ValueError("calibration registry must be a JSON object")
    expected_fields = {
        "schema_version",
        "corpus_id",
        "corpus_version",
        "corpus_digest",
        "records",
    }
    if set(value) != expected_fields or value.get("schema_version") != CALIBRATION_SCHEMA_VERSION:
        raise ValueError(f"calibration registry must use schema {CALIBRATION_SCHEMA_VERSION}")
    if (
        value.get("corpus_id") != identity.id
        or value.get("corpus_version") != identity.version
        or value.get("corpus_digest") != identity.digest
    ):
        raise ValueError("calibration registry corpus identity is stale or non-current")
    records_value = value.get("records")
    if not isinstance(records_value, list):
        raise ValueError("calibration registry records must be an array")
    records: dict[str, dict[str, Any]] = {}
    for record_value in records_value:
        record = _validate_record(record_value, identity=identity)
        task_id = str(record["task_id"])
        if task_id in records:
            raise ValueError(f"duplicate calibration task {task_id}")
        records[task_id] = record
    return CalibrationRegistry(records=records)


def calibration_activation_errors(
    *,
    identity: CorpusIdentity,
    lifecycle: LifecycleRegistry,
    registry: CalibrationRegistry,
) -> list[str]:
    errors: list[str] = []
    for task_id in sorted(lifecycle.task_ids("active")):
        record = registry.records.get(task_id)
        if record is None:
            errors.append(f"active task {task_id} has no current calibration record")
            continue
        configurations = record["configurations"]
        if len(configurations) < MINIMUM_CALIBRATION_CONFIGURATIONS:
            errors.append(
                f"active task {task_id} has fewer than {MINIMUM_CALIBRATION_CONFIGURATIONS} calibration configurations"
            )
        if any(
            configuration["valid_observation_count"]
            < MINIMUM_VALID_OBSERVATIONS_PER_CONFIGURATION
            for configuration in configurations
        ):
            errors.append(
                f"active task {task_id} lacks a valid observation in every calibration configuration"
            )
        review = record["review"]
        if review["decision"] != "approve":
            errors.append(f"active task {task_id} lacks an explicit approval decision")
        if review["accepted_alternatives_status"] not in {
            "reviewed-no-issue",
            "reviewed-issue-resolved",
        }:
            errors.append(f"active task {task_id} lacks accepted-alternative review")
        if review["evaluator_dispute_status"] not in {
            "reviewed-no-issue",
            "reviewed-issue-resolved",
        }:
            errors.append(f"active task {task_id} lacks evaluator-dispute review")
    return errors


def build_calibration_report(
    *,
    identity: CorpusIdentity,
    tasks: Sequence[Task],
    study_sources: Sequence[tuple[Path, Mapping[str, Any]]],
) -> dict[str, Any]:
    validated: list[tuple[Path, dict[str, Any], str]] = []
    cells: set[tuple[str, str, str]] = set()
    for path, raw_study in study_sources:
        study = validate_current_study(raw_study)
        metadata = study["metadata"]
        if (
            metadata.get("corpus_id") != identity.id
            or metadata.get("corpus_version") != identity.version
            or metadata.get("corpus_visibility") != identity.visibility
            or metadata.get("corpus_digest") != identity.digest
        ):
            raise ValueError(f"study {path} does not match the exact current corpus identity")
        configuration_id = str(metadata["configuration_id"])
        for trial in study["trials"]:
            observations = trial["observations"]
            observed_ids = {str(item["task_id"]) for item in observations}
            if observed_ids != set(identity.task_ids):
                raise ValueError(f"study {path} trial task matrix does not match the current corpus")
            for observation in observations:
                task_id = str(observation["task_id"])
                if observation.get("task_digest") != identity.task_digests.get(task_id):
                    raise ValueError(f"study {path} contains a stale task digest for {task_id}")
                cell = (configuration_id, str(trial["run_id"]), task_id)
                if cell in cells:
                    raise ValueError(
                        "duplicate calibration cell " + "/".join(cell)
                    )
                cells.add(cell)
        for attempt in study.get("attempts", []):
            if not isinstance(attempt, Mapping) or attempt.get("measurement_status") == "valid":
                continue
            run_id = _nonempty_string(attempt.get("run_id"), "attempt run_id")
            if attempt.get("corpus_digest") != identity.digest or attempt.get("configuration_id") != configuration_id:
                raise ValueError(f"study {path} attempt identity does not match its study")
            for observation in attempt.get("observations", []):
                if not isinstance(observation, Mapping):
                    raise ValueError(f"study {path} attempt observation is invalid")
                task_id = _nonempty_string(observation.get("task_id"), "attempt task_id")
                if task_id not in identity.task_digests:
                    raise ValueError(f"study {path} attempt contains an unknown task")
                if observation.get("task_digest") != identity.task_digests[task_id]:
                    raise ValueError(f"study {path} attempt contains a stale task digest for {task_id}")
                cell = (configuration_id, run_id, task_id)
                if cell in cells:
                    raise ValueError("duplicate calibration cell " + "/".join(cell))
                cells.add(cell)
        validated.append((path, study, _sha256_file(path)))

    task_evidence = [
        {
            "task_id": task.id,
            "category": task.category,
            "difficulty": task.difficulty,
            "criterion_ids": [criterion.id for criterion in task.criteria],
            "criterion_coverage": [],
        }
        for task in tasks
    ]
    health = build_corpus_health_report(
        corpus_digest=identity.digest,
        task_evidence=task_evidence,
        studies=[study for _, study, _ in validated],
    )
    configurations = sorted(
        {str(study["metadata"]["configuration_id"]) for _, study, _ in validated}
    )
    records: list[dict[str, Any]] = []
    for task in sorted(tasks, key=lambda item: item.id):
        configuration_summaries = []
        for configuration_id in configurations:
            run_ids: list[str] = []
            passes = 0
            timeouts = 0
            invalid_count = 0
            incomplete_count = 0
            artifact_digests: set[str] = set()
            for _, study, artifact_digest in validated:
                if study["metadata"]["configuration_id"] != configuration_id:
                    continue
                for trial in study["trials"]:
                    observation = next(
                        item for item in trial["observations"] if item["task_id"] == task.id
                    )
                    run_ids.append(str(trial["run_id"]))
                    passes += observation.get("passed") is True
                    timeouts += observation.get("agent_timeout") is True
                    artifact_digests.add(artifact_digest)
                for attempt in study.get("attempts", []):
                    if not isinstance(attempt, Mapping) or attempt.get("measurement_status") == "valid":
                        continue
                    status = attempt.get("measurement_status")
                    if status == "invalid":
                        invalid_count += 1
                    elif status == "incomplete":
                        incomplete_count += 1
                    else:
                        raise ValueError("calibration attempt has an unknown measurement status")
                    artifact_digests.add(artifact_digest)
            valid_count = len(run_ids)
            total_attempts = valid_count + invalid_count + incomplete_count
            configuration_summaries.append(
                {
                    "configuration_id": configuration_id,
                    "valid_observation_count": valid_count,
                    "run_ids": sorted(run_ids),
                    "study_artifact_sha256": sorted(artifact_digests),
                    "solve_rate": passes / valid_count if valid_count else None,
                    "timeout_rate": timeouts / valid_count if valid_count else None,
                    "invalid_attempt_count": invalid_count,
                    "incomplete_attempt_count": incomplete_count,
                    "invalid_attempt_rate": (
                        (invalid_count + incomplete_count) / total_attempts
                        if total_attempts
                        else None
                    ),
                }
            )
        task_health = health["tasks"][task.id]
        records.append(
            {
                "task_id": task.id,
                "task_digest": identity.task_digests[task.id],
                "corpus_id": identity.id,
                "corpus_version": identity.version,
                "corpus_digest": identity.digest,
                "configurations": configuration_summaries,
                "discrimination": task_health["discrimination"],
                "author_difficulty": task.difficulty,
                "empirical_difficulty": _empirical_difficulty(
                    task_health["empirical_solve_rate_band"]
                ),
                "review": {
                    "decision": "pending",
                    "reviewer": None,
                    "date": None,
                    "rationale": "",
                    "accepted_alternatives_status": "pending",
                    "evaluator_dispute_status": "pending",
                },
            }
        )
    return {
        "schema_version": CALIBRATION_REPORT_SCHEMA_VERSION,
        "corpus_id": identity.id,
        "corpus_version": identity.version,
        "corpus_digest": identity.digest,
        "minimums": {
            "configuration_count": MINIMUM_CALIBRATION_CONFIGURATIONS,
            "valid_observations_per_configuration": MINIMUM_VALID_OBSERVATIONS_PER_CONFIGURATION,
        },
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "records": records,
    }


def registry_payload_from_report(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "corpus_id": report["corpus_id"],
        "corpus_version": report["corpus_version"],
        "corpus_digest": report["corpus_digest"],
        "records": report["records"],
    }


def _validate_record(value: object, *, identity: CorpusIdentity) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("calibration record must be an object")
    fields = {
        "task_id",
        "task_digest",
        "corpus_id",
        "corpus_version",
        "corpus_digest",
        "configurations",
        "discrimination",
        "author_difficulty",
        "empirical_difficulty",
        "review",
    }
    if set(value) != fields:
        raise ValueError("calibration record fields are incomplete or unknown")
    task_id = _nonempty_string(value.get("task_id"), "calibration task_id")
    if task_id not in identity.task_digests:
        raise ValueError(f"calibration record names unknown task {task_id}")
    if value.get("task_digest") != identity.task_digests[task_id]:
        raise ValueError(f"calibration record task digest is stale for {task_id}")
    if (
        value.get("corpus_id") != identity.id
        or value.get("corpus_version") != identity.version
        or value.get("corpus_digest") != identity.digest
    ):
        raise ValueError(f"calibration record corpus identity is stale for {task_id}")
    configurations_value = value.get("configurations")
    if not isinstance(configurations_value, list):
        raise ValueError(f"{task_id}: calibration configurations must be an array")
    configurations = [_validate_configuration(item, task_id) for item in configurations_value]
    ids = [item["configuration_id"] for item in configurations]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{task_id}: duplicate calibration configuration")
    discrimination = value.get("discrimination")
    discrimination_fields = {
        "method",
        "method_version",
        "sampling_unit",
        "n",
        "configuration_count",
        "estimate",
        "unavailable_reason",
        "leave_one_task_out_statistic",
    }
    if not isinstance(discrimination, Mapping) or set(discrimination) != discrimination_fields:
        raise ValueError(f"{task_id}: discrimination fields are incomplete or unknown")
    review = _validate_review(value.get("review"), task_id)
    author_difficulty = _nonempty_string(value.get("author_difficulty"), f"{task_id}: author difficulty")
    empirical = value.get("empirical_difficulty")
    if empirical is not None and not isinstance(empirical, str):
        raise ValueError(f"{task_id}: empirical difficulty is invalid")
    return {**dict(value), "configurations": configurations, "discrimination": dict(discrimination), "review": review, "author_difficulty": author_difficulty}


def _validate_configuration(value: object, task_id: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{task_id}: calibration configuration must be an object")
    fields = {
        "configuration_id",
        "valid_observation_count",
        "run_ids",
        "study_artifact_sha256",
        "solve_rate",
        "timeout_rate",
        "invalid_attempt_count",
        "incomplete_attempt_count",
        "invalid_attempt_rate",
    }
    if set(value) != fields:
        raise ValueError(f"{task_id}: calibration configuration fields are incomplete or unknown")
    configuration_id = _nonempty_string(value.get("configuration_id"), f"{task_id}: configuration_id")
    digest = configuration_id.removeprefix("cfg-")
    if not configuration_id.startswith("cfg-") or len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise ValueError(
            f"{task_id}: configuration_id must use canonical cfg-<sha256> form"
        )
    valid_count = _nonnegative_int(value.get("valid_observation_count"), f"{task_id}: valid observation count")
    run_ids = _unique_strings(value.get("run_ids"), f"{task_id}: run_ids")
    if len(run_ids) != valid_count:
        raise ValueError(f"{task_id}/{configuration_id}: run IDs disagree with valid observation count")
    artifacts = _unique_strings(value.get("study_artifact_sha256"), f"{task_id}: artifact digests")
    if any(len(item) != 64 or any(character not in "0123456789abcdef" for character in item) for item in artifacts):
        raise ValueError(f"{task_id}: study artifact digest is invalid")
    invalid_count = _nonnegative_int(value.get("invalid_attempt_count"), f"{task_id}: invalid attempt count")
    incomplete_count = _nonnegative_int(value.get("incomplete_attempt_count"), f"{task_id}: incomplete attempt count")
    for field in ("solve_rate", "timeout_rate", "invalid_attempt_rate"):
        rate = value.get(field)
        if rate is not None and (isinstance(rate, bool) or not isinstance(rate, (int, float)) or not math.isfinite(float(rate)) or not 0 <= float(rate) <= 1):
            raise ValueError(f"{task_id}/{configuration_id}: {field} is invalid")
    if valid_count == 0 and (value.get("solve_rate") is not None or value.get("timeout_rate") is not None):
        raise ValueError(f"{task_id}/{configuration_id}: rates require valid observations")
    return dict(value)


def _validate_review(value: object, task_id: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{task_id}: calibration review must be an object")
    fields = {
        "decision",
        "reviewer",
        "date",
        "rationale",
        "accepted_alternatives_status",
        "evaluator_dispute_status",
    }
    if set(value) != fields:
        raise ValueError(f"{task_id}: calibration review fields are incomplete or unknown")
    decision = _nonempty_string(value.get("decision"), f"{task_id}: review decision")
    if decision not in REVIEW_DECISIONS:
        raise ValueError(f"{task_id}: unknown review decision")
    for field in ("accepted_alternatives_status", "evaluator_dispute_status"):
        if value.get(field) not in REVIEW_STATUSES:
            raise ValueError(f"{task_id}: {field} is invalid")
    reviewer = value.get("reviewer")
    date = value.get("date")
    rationale = value.get("rationale")
    if not isinstance(rationale, str):
        raise ValueError(f"{task_id}: review rationale must be a string")
    if decision == "pending":
        if reviewer is not None or date is not None:
            raise ValueError(f"{task_id}: pending review cannot name reviewer or date")
    else:
        _nonempty_string(reviewer, f"{task_id}: reviewer")
        date_value = _nonempty_string(date, f"{task_id}: review date")
        try:
            dt.date.fromisoformat(date_value)
        except ValueError as exc:
            raise ValueError(f"{task_id}: review date must be ISO-8601") from exc
        if not rationale.strip():
            raise ValueError(f"{task_id}: completed review requires rationale")
    return dict(value)


def _empirical_difficulty(solve_rate_band: object) -> str | None:
    if solve_rate_band is None:
        return None
    mapping = {"high": "easy", "mixed": "mixed", "low": "hard"}
    try:
        return mapping[str(solve_rate_band)]
    except KeyError as exc:
        raise ValueError("unknown empirical solve-rate band") from exc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _unique_strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be a string array")
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicates")
    return list(value)
