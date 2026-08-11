from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_SITE_METADATA = (
    "label",
    "model",
    "series",
    "effort",
    "marker",
    "kind",
    "agent_version",
    "corpus_revision",
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
) -> int:
    if minimum_trials < 1:
        raise ValueError("minimum_trials must be at least 1")
    if expected_configurations is not None and expected_configurations < 1:
        raise ValueError("expected_configurations must be at least 1")

    studies_dir = results_dir / "studies"
    study_paths = sorted(studies_dir.glob("*/summary.json"))
    if not study_paths:
        raise ValueError(f"no study summaries found under {studies_dir}")

    rows: list[dict[str, Any]] = []
    for study_path in study_paths:
        try:
            study = json.loads(study_path.read_text())
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read study summary {study_path}: {exc}") from exc

        metadata = study.get("metadata")
        if not isinstance(metadata, dict):
            raise ValueError(f"study summary {study_path} has no metadata object")
        if metadata.get("publish") is False:
            continue
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

        study_task_count = _positive_int(
            study.get("task_count"), f"{study_path}: task_count"
        )
        if task_count is not None and study_task_count != task_count:
            continue
        trials = study.get("trials")
        if not isinstance(trials, list) or not trials:
            raise ValueError(f"study summary {study_path} has no trials")

        configuration_id = (
            f"{metadata['series']}-{metadata['effort']}-{study_task_count}"
        )
        study_id = _nonempty_string(
            study.get("study_id", study_path.parent.name),
            f"{study_path}: study_id",
        )
        for trial_number, trial in enumerate(trials, start=1):
            if not isinstance(trial, dict):
                raise ValueError(
                    f"study summary {study_path} contains a non-object trial"
                )
            run_id = _nonempty_string(trial.get("run_id"), f"{study_path}: run_id")
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
                    "corpusRevision": metadata["corpus_revision"],
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
