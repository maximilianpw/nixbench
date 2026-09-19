from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from .reporting import (
    build_configuration_report,
    build_study_report,
    load_study_summary,
)


REQUIRED_SITE_METADATA = (
    "label",
    "model",
    "series",
    "effort",
    "marker",
    "kind",
    "agent_version",
    "host",
    "network",
)


def export_studies_for_site(
    results_dir: Path,
    output_path: Path,
    *,
    task_count: int | None = None,
    minimum_trials: int = 1,
    expected_configurations: int | None = None,
    merge_existing: bool = False,
    allow_legacy_protocol: bool = False,
) -> int:
    if minimum_trials < 1:
        raise ValueError("minimum_trials must be at least 1")
    if expected_configurations is not None and expected_configurations < 1:
        raise ValueError("expected_configurations must be at least 1")

    studies_dir = results_dir / "studies"
    study_paths = sorted(studies_dir.glob("*/summary.json"))
    if not study_paths:
        raise ValueError(f"no study summaries found under {studies_dir}")

    loaded_studies: dict[Path, dict[str, Any]] = {}
    for study_path in study_paths:
        try:
            shallow = json.loads(study_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read study summary {study_path}: {exc}") from exc
        if not isinstance(shallow, dict):
            raise ValueError(f"study summary {study_path} must be a JSON object")
        metadata = shallow.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("publish") is False:
            continue
        visibility = metadata.get("corpus_visibility")
        if visibility in {"private-heldout", "retired"}:
            raise ValueError(
                f"study summary {study_path} with {visibility} visibility cannot be exported to the public site"
            )
        present_site_metadata = [
            key for key in REQUIRED_SITE_METADATA if metadata.get(key)
        ]
        if not present_site_metadata:
            continue
        missing = [key for key in REQUIRED_SITE_METADATA if not metadata.get(key)]
        if missing:
            raise ValueError(
                f"study summary {study_path} is missing site metadata: {', '.join(missing)}"
            )
        shallow_trials = shallow.get("trials")
        shallow_trial_count = shallow.get(
            "trial_count", len(shallow_trials) if isinstance(shallow_trials, list) else None
        )
        if shallow_trial_count == 0 and shallow_trials == []:
            continue
        loaded_studies[study_path] = load_study_summary(study_path)
    report_groups: dict[tuple[str, str] | tuple[str, Path], list[dict[str, Any]]] = {}
    group_key_by_path: dict[Path, tuple[str, str] | tuple[str, Path]] = {}
    for study_path, study in loaded_studies.items():
        metadata = study.get("metadata")
        configuration_id = metadata.get("configuration_id") if isinstance(metadata, dict) else None
        corpus_digest = metadata.get("corpus_digest") if isinstance(metadata, dict) else None
        key: tuple[str, str] | tuple[str, Path]
        participates = isinstance(metadata, dict)
        if (
            participates
            and isinstance(configuration_id, str)
            and isinstance(corpus_digest, str)
        ):
            key = (corpus_digest, configuration_id)
        else:
            key = ("study", study_path)
        group_key_by_path[study_path] = key
        report_groups.setdefault(key, []).append(study)
    canonical_reports = {
        key: (
            build_configuration_report(studies)
            if len(studies) > 1 and isinstance(key[1], str)
            else build_study_report(studies[0])
        )
        for key, studies in report_groups.items()
    }

    rows: list[dict[str, Any]] = []
    for study_path, study in loaded_studies.items():

        metadata = study.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"study summary {study_path} has no metadata object")
        trials = study.get("trials")
        trial_count = study.get("trial_count", len(trials) if isinstance(trials, list) else None)
        if trial_count == 0 and trials == []:
            continue
        study_task_count = _positive_int(
            study.get("task_count"), f"{study_path}: task_count"
        )
        if task_count is not None and study_task_count != task_count:
            continue
        if not isinstance(trials, list) or not trials:
            raise ValueError(f"study summary {study_path} has no trials")
        study_id = _nonempty_string(
            study.get("study_id", study_path.parent.name),
            f"{study_path}: study_id",
        )
        canonical_report = canonical_reports[group_key_by_path[study_path]]
        stratum_counts = _export_stratum_counts(canonical_report)

        protocol_complete = metadata.get("protocol_complete") is True
        if protocol_complete:
            required_identity = (
                "corpus_id",
                "corpus_version",
                "corpus_digest",
                "protocol_id",
                "configuration_id",
                "timing_environment_id",
                "completion_attestation",
                "agent_adapter",
                "agent_adapter_sha256",
                "attestation_trust",
                "wrapper_prompt_sha256",
                "agent_command_sha256",
            )
            missing_identity = [
                key for key in required_identity if not metadata.get(key)
            ]
            if missing_identity:
                raise ValueError(
                    f"study summary {study_path} is missing identity metadata: "
                    + ", ".join(missing_identity)
                )
            configuration_id = _nonempty_string(
                metadata["configuration_id"], f"{study_path}: configuration_id"
            )
            corpus_digest = _nonempty_string(
                metadata["corpus_digest"], f"{study_path}: corpus_digest"
            )
            _sha256_string(
                metadata["wrapper_prompt_sha256"],
                f"{study_path}: wrapper_prompt_sha256",
            )
            _sha256_string(
                metadata["agent_command_sha256"],
                f"{study_path}: agent_command_sha256",
            )
            if metadata["completion_attestation"] != "required":
                raise ValueError(
                    f"{study_path}: completion_attestation must be required"
                )
            if metadata["attestation_trust"] == "provisional-same-uid" and metadata.get(
                "corpus_visibility"
            ) in {"private", "held-out", "private-heldout"}:
                raise ValueError(
                    f"{study_path}: held-out publication requires approved isolation evidence"
                )
        elif allow_legacy_protocol:
            stored_configuration = metadata.get("configuration_id")
            stored_corpus = metadata.get("corpus_digest")
            if stored_configuration is not None or stored_corpus is not None:
                configuration_id = _nonempty_string(
                    stored_configuration, f"{study_path}: configuration_id"
                )
                corpus_digest = _nonempty_string(
                    stored_corpus, f"{study_path}: corpus_digest"
                )
            else:
                configuration_id = f"legacy-{study_id}"
                corpus_digest = None
        else:
            raise ValueError(
                f"study summary {study_path} has an incomplete legacy protocol; "
                "use --allow-legacy-protocol only for explicit compatibility exports"
            )
        for trial_number, trial in enumerate(trials, start=1):
            if not isinstance(trial, dict):
                raise ValueError(
                    f"study summary {study_path} contains a non-object trial"
                )
            run_id = _nonempty_string(trial.get("run_id"), f"{study_path}: run_id")
            measurement_status = trial.get("measurement_status", "valid")
            if measurement_status != "valid":
                raise ValueError(
                    f"study summary {study_path} contains an invalid or incomplete trial: {run_id}"
                )
            scoring_schema = trial.get("scoring_schema", "legacy-binary")
            if (
                protocol_complete
                and scoring_schema != "criteria-v2"
                and not allow_legacy_protocol
            ):
                raise ValueError(
                    f"study summary {study_path} uses legacy scoring for current publication; "
                    "use --allow-legacy-protocol only for an explicit compatibility export"
                )
            has_stored_identity = corpus_digest is not None
            if has_stored_identity and (
                trial.get("configuration_id") != configuration_id
                or trial.get("corpus_digest") != corpus_digest
            ):
                raise ValueError(
                    f"study summary {study_path} trial {run_id} has mixed corpus or protocol identities"
                )
            passed_tasks = _nonnegative_int(
                trial.get("passed_tasks"), f"{study_path}: passed_tasks"
            )
            failed_tasks = _nonnegative_int(
                trial.get("failed_tasks"), f"{study_path}: failed_tasks"
            )
            if passed_tasks + failed_tasks != study_task_count:
                raise ValueError(
                    f"study summary {study_path} trial {run_id} has inconsistent task totals"
                )

            agent_time_seconds = _nonnegative_number(
                trial.get("agent_time_seconds"),
                f"{study_path}: agent_time_seconds",
            )
            score = _nonnegative_number(trial.get("score"), f"{study_path}: score")
            max_score = _nonnegative_number(
                trial.get("max_score"), f"{study_path}: max_score"
            )
            timeouts = _nonnegative_int(
                trial.get("timeouts"), f"{study_path}: timeouts"
            )

            rows.append(
                {
                    "id": f"{configuration_id}-{run_id}",
                    "configurationId": configuration_id,
                    "agent": metadata["label"],
                    "agentVersion": metadata["agent_version"],
                    "model": metadata["model"],
                    "kind": metadata["kind"],
                    "corpus": f"{study_task_count}-task corpus",
                    "corpusRevision": metadata.get("corpus_revision"),
                    "corpusId": metadata.get("corpus_id"),
                    "corpusVersion": metadata.get("corpus_version"),
                    "corpusDigest": corpus_digest,
                    "corpusVisibility": metadata.get("corpus_visibility"),
                    "protocolId": metadata.get("protocol_id"),
                    "protocolSchemaVersion": metadata.get("protocol_schema_version"),
                    "protocolComplete": protocol_complete,
                    "modelIdentityEvidence": metadata.get("model_identity_evidence"),
                    "wrapperPromptSha256": metadata.get("wrapper_prompt_sha256"),
                    "agentCommandSha256": metadata.get("agent_command_sha256"),
                    "timingEnvironmentId": metadata.get("timing_environment_id"),
                    "completionAttestation": metadata.get("completion_attestation"),
                    "agentAdapter": metadata.get("agent_adapter"),
                    "agentAdapterSha256": metadata.get("agent_adapter_sha256"),
                    "attestationTrust": metadata.get("attestation_trust"),
                    "scoringSchema": scoring_schema,
                    "host": metadata["host"],
                    "network": metadata["network"],
                    "platform": metadata.get("platform"),
                    "system": metadata.get("system"),
                    "agentTimeoutSeconds": metadata.get("agent_timeout_seconds"),
                    "studyId": study_id,
                    "runId": run_id,
                    "marker": metadata["marker"],
                    "series": metadata["series"],
                    "effort": metadata["effort"],
                    "trial": trial_number,
                    "provenance": "trial",
                    "passRate": round((passed_tasks / study_task_count) * 100),
                    "score": score,
                    "maxScore": max_score,
                    "agentTimeSeconds": agent_time_seconds,
                    "agentTimeLabel": _format_duration(agent_time_seconds),
                    "failed": failed_tasks,
                    "timeouts": timeouts,
                    "completedTasks": study_task_count,
                    "totalTasks": study_task_count,
                    "status": "complete",
                    "observations": trial.get("observations"),
                    "aggregateOnly": canonical_report["aggregate_only"],
                    "canonicalReport": canonical_report,
                    "invalidMeasurementCount": canonical_report["attempts"]["invalid_count"],
                    "incompleteAttemptCount": canonical_report["attempts"]["incomplete_count"],
                    "stratumCounts": stratum_counts,
                    "descriptiveOnly": (
                        canonical_report["strata"]["whole_corpus"]["descriptive_only"]
                        if canonical_report.get("strata")
                        and canonical_report["strata"].get("whole_corpus")
                        else None
                    ),
                }
            )

    if not rows:
        corpus_label = (
            f" for the {task_count}-task corpus" if task_count is not None else ""
        )
        raise ValueError(f"no exportable study trials found{corpus_label}")

    duplicate_run_ids = sorted(
        run_id for run_id, count in Counter(row["runId"] for row in rows).items() if count > 1
    )
    if duplicate_run_ids:
        raise ValueError(
            "duplicate run IDs in exportable studies: " + ", ".join(duplicate_run_ids)
        )

    corpus_by_configuration: dict[str, str | None] = {}
    for row in rows:
        configuration_id = row["configurationId"]
        corpus_digest = row["corpusDigest"]
        previous = corpus_by_configuration.setdefault(configuration_id, corpus_digest)
        if previous != corpus_digest:
            raise ValueError(
                f"configuration {configuration_id} contains mixed corpus digests"
            )

    configuration_counts = Counter(row["configurationId"] for row in rows)
    if (
        expected_configurations is not None
        and len(configuration_counts) != expected_configurations
    ):
        raise ValueError(
            f"expected {expected_configurations} configurations, found {len(configuration_counts)}"
        )
    incomplete = {
        configuration_id: count
        for configuration_id, count in configuration_counts.items()
        if count < minimum_trials
    }
    if incomplete:
        detail = ", ".join(
            f"{key}={count}" for key, count in sorted(incomplete.items())
        )
        raise ValueError(
            f"configurations below minimum_trials={minimum_trials}: {detail}"
        )

    if merge_existing and output_path.exists():
        rows = _merge_existing_rows(output_path, rows)
        duplicate_run_ids = sorted(
            run_id
            for run_id, count in Counter(row["runId"] for row in rows).items()
            if count > 1
        )
        if duplicate_run_ids:
            raise ValueError(
                "duplicate run IDs after merging existing output: "
                + ", ".join(duplicate_run_ids)
            )

    rows.sort(
        key=lambda row: (row["corpus"], row["series"], row["effort"], row["runId"])
    )
    trial_numbers: Counter[str] = Counter()
    for row in rows:
        trial_numbers[row["configurationId"]] += 1
        row["trial"] = trial_numbers[row["configurationId"]]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return len(rows)


def _merge_existing_rows(
    output_path: Path, incoming_rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    try:
        existing = json.loads(output_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read existing site data {output_path}: {exc}") from exc
    if not isinstance(existing, list) or not all(isinstance(row, dict) for row in existing):
        raise ValueError(f"existing site data {output_path} must be an array of objects")

    incoming_run_ids = {row["runId"] for row in incoming_rows}
    rows_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(existing):
        row_id = _nonempty_string(row.get("id"), f"{output_path}: row {index}: id")
        run_id = _nonempty_string(row.get("runId"), f"{output_path}: row {index}: runId")
        if run_id in incoming_run_ids:
            continue
        if row_id in rows_by_id:
            raise ValueError(f"duplicate row ID in existing site data: {row_id}")
        rows_by_id[row_id] = row
    for row in incoming_rows:
        rows_by_id[row["id"]] = row
    return list(rows_by_id.values())


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _sha256_string(value: object, label: str) -> str:
    text = _nonempty_string(value, label)
    if re.fullmatch(r"[0-9a-f]{64}", text) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return text


def _positive_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError(f"{label} must be a positive integer")
    return value


def _nonnegative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def _nonnegative_number(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} must be a non-negative number")
    return float(value)


def _format_duration(seconds: float) -> str:
    rounded = round(seconds)
    minutes, remainder = divmod(rounded, 60)
    if minutes < 60:
        return f"{minutes}m {remainder:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m {remainder:02d}s"


def _export_stratum_counts(report: dict[str, Any]) -> dict[str, Any] | None:
    strata = report.get("strata")
    if not isinstance(strata, dict) or not isinstance(strata.get("whole_corpus"), dict):
        return None
    whole = strata["whole_corpus"]
    return {
        "wholeCorpusTaskCount": whole["task_count"],
        "wholeCorpusValidObservationCount": whole["valid_observation_count"],
        "wholeCorpusTimeoutCount": whole["timeout_count"],
        "wholeCorpusTimeoutRate": whole["timeout_rate"],
        "categories": {
            key: {
                "taskCount": value["task_count"],
                "validObservationCount": value["valid_observation_count"],
                "timeoutCount": value["timeout_count"],
                "timeoutRate": value["timeout_rate"],
                "descriptiveOnly": value["descriptive_only"],
            }
            for key, value in strata["categories"].items()
        },
        "difficulties": {
            key: {
                "taskCount": value["task_count"],
                "validObservationCount": value["valid_observation_count"],
                "timeoutCount": value["timeout_count"],
                "timeoutRate": value["timeout_rate"],
                "descriptiveOnly": value["descriptive_only"],
            }
            for key, value in strata["difficulties"].items()
        },
    }
