from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from .adapters import get_trusted_adapter
from .corpus import CorpusIdentity, identify_corpus
from .isolation import APPROVED_HELDOUT_PROFILE, APPROVED_PREFLIGHT_EVIDENCE
from .reporting import (
    CORPUS_HEALTH_SCHEMA_VERSION,
    FIXED_CORPUS_METHOD_VERSION,
    REPORT_SCHEMA_VERSION,
    RESAMPLING_METHOD_VERSION,
    WILSON_METHOD_VERSION,
    build_study_report,
)
from .runner import TaskRunResult, run_task
from .task import Task, TaskError, iter_tasks, load_task

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


RELEASE_TOOL_SCHEMA_VERSION = 1
RELEASE_MANIFEST_SCHEMA_VERSION = 1
REQUIRED_PROTOCOL_SCHEMA_VERSION = 2
RUNTIME_SAFETY_FRACTION = 0.8
MINIMUM_PUBLICATION_TASKS = 5
MINIMUM_PUBLICATION_OBSERVATIONS = 20


def release_tool_digest() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def health_report_provenance(
    corpus_digest: str, evidence: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    return {
        "corpus_digest": corpus_digest,
        "scoring_schema": "criteria-v2",
        "tool_versions": _tool_versions(),
        "release_tool_sha256": release_tool_digest(),
        "health_evidence_sha256": _hash_json([dict(item) for item in evidence]),
    }


def load_verified_health_evidence(
    path: Path, *, corpus_root: Path
) -> list[dict[str, Any]]:
    if os.environ.get("CI"):
        raise ValueError("--health-report is forbidden in release CI; recompute evidence")
    try:
        payload = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read health report {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("health report must be a JSON object")
    evidence = payload.get("release_evidence")
    if not isinstance(evidence, list) or not all(
        isinstance(item, dict) for item in evidence
    ):
        raise ValueError("health report has no verifiable release evidence")
    identity = identify_corpus(corpus_root / "tasks", corpus_root / "corpus.toml")
    expected = health_report_provenance(identity.digest, evidence)
    if payload.get("release_provenance") != expected:
        raise ValueError("health report provenance is stale or unverifiable")
    return [dict(item) for item in evidence]


def check_release(
    corpus_root: Path,
    *,
    health_evidence: Sequence[Mapping[str, Any]] | None = None,
    verify_manifest: bool = True,
    system: str | None = None,
) -> dict[str, Any]:
    root = corpus_root.resolve()
    try:
        identity = identify_corpus(root / "tasks", root / "corpus.toml")
        tasks = [
            task
            for task in iter_tasks(root / "tasks")
            if task.supports_system(system)
        ]
    except (TaskError, ValueError):
        return {
            "schema_version": RELEASE_TOOL_SCHEMA_VERSION,
            "eligible": False,
            "corpus": None,
            "required_protocol_schema_version": REQUIRED_PROTOCOL_SCHEMA_VERSION,
            "gates": [
                {
                    "name": "valid-corpus-identity",
                    "passed": False,
                    "reason": "corpus manifest or active task structure is invalid",
                }
            ],
            "strata": None,
            "warnings": [],
            "policy": {"governance": "docs/benchmark-governance.md"},
            "tool_versions": _tool_versions(),
            "release_gate_result_digest": None,
        }
    if not tasks:
        raise ValueError("release check selected no tasks")
    vocabulary = _load_category_vocabulary(root / "corpus" / "category-vocabulary.toml")
    deprecations = _load_deprecations(root / "corpus" / "task-deprecations.toml")
    lifecycle_valid = True
    try:
        quarantined = _load_quarantined_tasks(root / "corpus" / "task-lifecycle.toml")
    except ValueError:
        lifecycle_valid = False
        quarantined = set()
    evidence = (
        [dict(item) for item in health_evidence]
        if health_evidence is not None
        else collect_health_evidence(tasks, root / "contracts")
    )
    evidence_by_task = {
        str(item.get("task_id")): item
        for item in evidence
        if isinstance(item.get("task_id"), str)
    }
    gates: list[dict[str, Any]] = []

    _add_gate(
        gates,
        "valid-corpus-identity",
        identity.task_count == len(iter_tasks(root / "tasks")),
        "corpus manifest and content identity are valid",
        "corpus task count does not match the loaded corpus",
    )
    invalid_categories = sorted({task.category for task in tasks} - vocabulary)
    _add_gate(
        gates,
        "controlled-category-vocabulary",
        not invalid_categories,
        "all active task categories use the controlled vocabulary",
        "active tasks use categories outside corpus/category-vocabulary.toml",
    )
    missing_evidence = sorted(set(identity.task_ids) - set(evidence_by_task))
    extra_evidence = sorted(set(evidence_by_task) - set(identity.task_ids))
    _add_gate(
        gates,
        "complete-health-evidence",
        not missing_evidence and not extra_evidence,
        "health evidence covers every active task exactly once",
        "health evidence does not match the active corpus task set",
    )
    _add_gate(
        gates,
        "reference-and-starter-outcomes",
        all(
            item.get("reference_full_score") is True
            and item.get("starter_rejected") is True
            for item in evidence
        ),
        "references earn full score and starters reject validly",
        "a reference or starter outcome does not meet the release contract",
    )
    _add_gate(
        gates,
        "independent-contract-fixtures",
        all(
            int(item.get("pass_fixture_count", 0)) >= 1
            and int(item.get("reject_fixture_count", 0)) >= 1
            and item.get("contract_outcomes_match") is True
            for item in evidence
        ),
        "every task has matching passing and rejecting fixtures",
        "every task needs at least one passing fixture, one rejecting fixture, and matching outcomes",
    )
    _add_gate(
        gates,
        "required-rubric-coverage",
        all(
            set(_string_list(item.get("criterion_ids", [])))
            <= set(_string_list(item.get("criterion_coverage", [])))
            for item in evidence
        ),
        "contract fixtures map every required rubric criterion",
        "one or more required rubric criteria lack contract fixture coverage",
    )
    _add_gate(
        gates,
        "deterministic-evaluators",
        all(item.get("evaluator_deterministic") is True for item in evidence),
        "reference and representative fixture runs are deterministic",
        "an evaluator produced different results across repeated runs",
    )
    _add_gate(
        gates,
        "valid-health-measurements",
        all(int(item.get("invalid_measurement_count", 0)) == 0 for item in evidence),
        "release health runs contain no invalid measurements",
        "release health evidence contains an invalid measurement",
    )
    runtime_safe = all(_runtime_has_margin(item) for item in evidence)
    _add_gate(
        gates,
        "evaluator-runtime-margin",
        runtime_safe,
        f"evaluator runtime stays below {RUNTIME_SAFETY_FRACTION:.0%} of timeout",
        f"an evaluator reached or exceeded {RUNTIME_SAFETY_FRACTION:.0%} of its timeout",
    )
    _add_gate(
        gates,
        "no-active-known-issue-skips",
        all(int(item.get("known_issue_count", 0)) == 0 for item in evidence),
        "active contract fixtures contain no known-issue skips",
        "active contract fixtures still contain known-issue skips",
    )
    active_ids = set(identity.task_ids)
    invalid_deprecations = sorted(active_ids & set(deprecations))
    _add_gate(
        gates,
        "recorded-task-deprecations",
        not invalid_deprecations,
        "deprecation records do not conflict with active tasks",
        "an active task is also recorded as deprecated",
    )
    _add_gate(
        gates,
        "valid-task-lifecycle-policy",
        lifecycle_valid,
        "task lifecycle policy is valid",
        "corpus/task-lifecycle.toml is missing or invalid",
    )
    _add_gate(
        gates,
        "no-active-quarantined-tasks",
        lifecycle_valid and not (active_ids & quarantined),
        "quarantined tasks do not contribute to the active corpus",
        "a quarantined task remains in the active scored corpus",
    )
    release_note = root / "docs" / "releases" / f"{identity.version}.md"
    _add_gate(
        gates,
        "release-note",
        release_note.is_file() and bool(release_note.read_text().strip()),
        "the corpus version has a release note",
        "the corpus version needs a nonempty release note",
    )

    category_counts = Counter(task.category for task in tasks)
    difficulty_counts = Counter(task.difficulty for task in tasks)
    report: dict[str, Any] = {
        "schema_version": RELEASE_TOOL_SCHEMA_VERSION,
        "eligible": False,
        "corpus": _safe_corpus_identity(identity),
        "required_protocol_schema_version": REQUIRED_PROTOCOL_SCHEMA_VERSION,
        "gates": gates,
        "strata": {
            "categories": dict(sorted(category_counts.items())),
            "difficulties": dict(sorted(difficulty_counts.items())),
            "descriptive_only_categories": sorted(
                category for category, count in category_counts.items() if count < 5
            ),
        },
        "warnings": (
            ["descriptive-only-category"]
            if any(count < 5 for count in category_counts.values())
            else []
        ),
        "policy": {
            "governance": "docs/benchmark-governance.md",
            "category_vocabulary": "corpus/category-vocabulary.toml",
            "task_deprecations": "corpus/task-deprecations.toml",
            "task_lifecycle": "corpus/task-lifecycle.toml",
        },
        "tool_versions": _tool_versions(),
    }
    report["release_gate_result_digest"] = _release_gate_digest(
        report, root=root, evidence=evidence
    )

    if verify_manifest:
        manifest_path = root / "corpus" / "releases" / f"{identity.version}.json"
        manifest_ok, manifest_reason = _verify_release_manifest(
            manifest_path, report
        )
        _add_gate(
            gates,
            "checked-release-manifest",
            manifest_ok,
            "checked release manifest matches corpus and gate evidence",
            manifest_reason,
        )
    report["eligible"] = all(gate["passed"] for gate in gates)
    return report


def build_release_manifest(
    release_report: Mapping[str, Any],
    *,
    previous_version: str | None,
    previous_manifest: Mapping[str, Any] | None = None,
    compatibility: str = "major",
    release_date: str | None = None,
) -> dict[str, Any]:
    if release_report.get("eligible") is not True:
        raise ValueError("cannot build a release manifest from an ineligible report")
    corpus = release_report.get("corpus")
    if not isinstance(corpus, Mapping):
        raise ValueError("release report has no corpus identity")
    visibility = str(corpus.get("visibility"))
    task_ids = _string_list(corpus.get("task_ids", []))
    task_digests = corpus.get("task_digests", {})
    if not isinstance(task_digests, Mapping):
        task_digests = {}
    if visibility == "public":
        active_tasks = task_ids
        manifest_task_digests = {
            task_id: str(task_digests[task_id])
            for task_id in active_tasks
            if task_id in task_digests
        }
    else:
        active_tasks = _string_list(corpus.get("opaque_task_hashes", []))
        manifest_task_digests = {}
    strata = release_report.get("strata", {})
    trusted_isolation = None
    if visibility == "private-heldout":
        adapter = get_trusted_adapter("codex-json-bwrap")
        trusted_isolation = {
            "profile": APPROVED_HELDOUT_PROFILE,
            "adapter": adapter.id,
            "adapter_sha256": adapter.sha256,
            "attestation_trust": adapter.trust,
            "preflight_evidence": APPROVED_PREFLIGHT_EVIDENCE,
        }
    if previous_version is None:
        added_tasks = active_tasks
        changed_tasks: list[str] = []
        deprecated_tasks: list[str] = []
    else:
        if not isinstance(previous_manifest, Mapping):
            raise ValueError(
                "a previous release manifest is required to classify task changes"
            )
        if previous_manifest.get("corpus_version") != previous_version:
            raise ValueError("previous release manifest version does not match")
        previous_active = set(_string_list(previous_manifest.get("active_tasks")))
        previous_digests = previous_manifest.get("task_digests")
        if not isinstance(previous_digests, Mapping):
            raise ValueError("previous release manifest has no task digest map")
        current_active = set(active_tasks)
        added_tasks = sorted(current_active - previous_active)
        deprecated_tasks = sorted(previous_active - current_active)
        changed_tasks = sorted(
            task_id
            for task_id in current_active & previous_active
            if manifest_task_digests.get(task_id) != previous_digests.get(task_id)
        )
    return {
        "schema_version": RELEASE_MANIFEST_SCHEMA_VERSION,
        "corpus_id": corpus.get("id"),
        "corpus_version": corpus.get("version"),
        "corpus_digest": corpus.get("digest"),
        "visibility": visibility,
        "release_date": release_date or dt.date.today().isoformat(),
        "task_count": corpus.get("task_count"),
        "category_counts": dict(strata.get("categories", {})),
        "difficulty_counts": dict(strata.get("difficulties", {})),
        "scoring_schema": "criteria-v2",
        "reporting": _tool_versions(),
        "release_gate_result_digest": release_report.get(
            "release_gate_result_digest"
        ),
        "required_protocol_schema_version": release_report.get(
            "required_protocol_schema_version"
        ),
        "previous_version": previous_version,
        "compatibility": compatibility,
        "active_tasks": active_tasks,
        "task_digests": manifest_task_digests,
        "added_tasks": added_tasks,
        "changed_tasks": changed_tasks,
        "deprecated_tasks": deprecated_tasks,
        "task_count_restricted": visibility != "public",
        "trusted_isolation": trusted_isolation,
    }


def check_publication(
    study: Mapping[str, Any], *, release_manifest: Mapping[str, Any]
) -> dict[str, Any]:
    metadata = study.get("metadata")
    reasons: list[str] = []
    if not isinstance(metadata, Mapping):
        return {"eligible": False, "reasons": ["study metadata is missing"]}
    if metadata.get("corpus_digest") != release_manifest.get("corpus_digest"):
        reasons.append("study corpus digest does not match the release manifest")
    if metadata.get("corpus_id") != release_manifest.get("corpus_id"):
        reasons.append("study corpus ID does not match the release manifest")
    if metadata.get("corpus_version") != release_manifest.get("corpus_version"):
        reasons.append("study corpus version does not match the release manifest")
    manifest_visibility = release_manifest.get("visibility")
    if metadata.get("corpus_visibility") != manifest_visibility:
        reasons.append("study visibility does not match the release manifest")
    if metadata.get("protocol_complete") is not True:
        reasons.append("publication requires a complete configuration identity")
    identity_fields = (
        "configuration_id",
        "protocol_id",
        "protocol_schema_version",
        "wrapper_prompt_sha256",
        "agent_command_sha256",
        "agent_adapter",
        "agent_adapter_sha256",
        "attestation_trust",
    )
    if any(not metadata.get(field) for field in identity_fields):
        reasons.append("publication configuration identity is incomplete")
    adapter_id = metadata.get("agent_adapter")
    try:
        adapter = get_trusted_adapter(str(adapter_id))
    except ValueError:
        reasons.append("publication agent adapter is not registered")
        adapter = None
    if adapter is not None and metadata.get("agent_adapter_sha256") != adapter.sha256:
        reasons.append("study adapter digest does not match the registered adapter")
    if metadata.get("completion_attestation") != "required":
        reasons.append("publication requires completion attestation")
    required_protocol = release_manifest.get("required_protocol_schema_version")
    if metadata.get("protocol_schema_version") != required_protocol:
        reasons.append("study protocol schema does not match the corpus release")
    expected_task_count = release_manifest.get("task_count")
    if study.get("task_count") != expected_task_count:
        reasons.append("study task count does not match the release manifest")
    trials = study.get("trials")
    trial_task_sets: list[set[str]] = []
    if not isinstance(trials, list) or not trials:
        reasons.append("publication requires at least one complete trial")
    else:
        for trial in trials:
            if not isinstance(trial, Mapping):
                reasons.append("publication trial is not an object")
                continue
            observations = trial.get("observations")
            observation_ids = (
                [item.get("task_id") for item in observations]
                if isinstance(observations, list)
                and all(isinstance(item, Mapping) for item in observations)
                else []
            )
            if (
                trial.get("measurement_status") != "valid"
                or trial.get("scoring_schema") != "criteria-v2"
                or trial.get("task_count") != expected_task_count
                or not isinstance(observations, list)
                or len(observations) != expected_task_count
                or len(observation_ids) != len(set(observation_ids))
                or any(not isinstance(task_id, str) or not task_id for task_id in observation_ids)
                or any(
                    not isinstance(item, Mapping)
                    or item.get("measurement_status") != "valid"
                    for item in observations
                )
            ):
                reasons.append("publication contains an invalid or incomplete trial")
                break
            trial_task_sets.append(set(observation_ids))
    if trial_task_sets and any(
        task_set != trial_task_sets[0] for task_set in trial_task_sets[1:]
    ):
        reasons.append("publication trials do not contain the same task matrix")
    if isinstance(trials, list):
        trial_run_ids = [
            trial.get("run_id")
            for trial in trials
            if isinstance(trial, Mapping)
        ]
        if (
            len(trial_run_ids) != len(trials)
            or any(
                not isinstance(run_id, str) or not run_id
                for run_id in trial_run_ids
            )
            or len(trial_run_ids) != len(set(trial_run_ids))
        ):
            reasons.append("publication trial run IDs are missing or duplicated")
    attempts = study.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        reasons.append("publication requires a complete attempts ledger")
    elif any(
        not isinstance(attempt, Mapping)
        or attempt.get("measurement_status") != "valid"
        or attempt.get("included_in_trials") is not True
        for attempt in attempts
    ):
        reasons.append("publication contains invalid or incomplete attempts")
    else:
        trial_run_ids = (
            {
                str(trial.get("run_id"))
                for trial in trials
                if isinstance(trial, Mapping)
                and isinstance(trial.get("run_id"), str)
            }
            if isinstance(trials, list)
            else set()
        )
        attempt_run_ids = {
            str(attempt.get("run_id"))
            for attempt in attempts
            if isinstance(attempt, Mapping)
            and isinstance(attempt.get("run_id"), str)
        }
        if attempt_run_ids != trial_run_ids or len(attempt_run_ids) != len(attempts):
            reasons.append("publication attempts ledger does not match its trials")
    if manifest_visibility == "private-heldout":
        isolation = release_manifest.get("trusted_isolation")
        isolation_valid = (
            isinstance(isolation, Mapping)
            and isolation.get("profile") == APPROVED_HELDOUT_PROFILE
            and isolation.get("adapter") == "codex-json-bwrap"
            and isolation.get("attestation_trust") == "approved-linux-bwrap-v1"
            and isolation.get("preflight_evidence") == APPROVED_PREFLIGHT_EVIDENCE
            and metadata.get("isolation_profile") == isolation.get("profile")
            and metadata.get("agent_adapter") == isolation.get("adapter")
            and metadata.get("attestation_trust") == isolation.get("attestation_trust")
        )
        if not isolation_valid:
            reasons.append(
                "held-out publication requires approved held-out isolation and successful preflight evidence"
            )
        if not isinstance(isolation, Mapping) or metadata.get(
            "agent_adapter_sha256"
        ) != isolation.get("adapter_sha256"):
            reasons.append("study adapter digest does not match trusted release manifest")
        if isinstance(trials, list):
            for trial in trials:
                status = trial.get("agent_status") if isinstance(trial, Mapping) else None
                if (
                    not isinstance(status, Mapping)
                    or status.get("task_count") != expected_task_count
                    or status.get("preflight_successful") is not True
                    or status.get("completed") is not True
                    or not isinstance(isolation, Mapping)
                    or status.get("preflight_evidence")
                    != isolation.get("preflight_evidence")
                ):
                    reasons.append(
                        "held-out publication trial has missing or invalid agent status evidence"
                    )
                    break
    return {"eligible": not reasons, "reasons": reasons}


def export_publication_bundle(
    study: Mapping[str, Any],
    *,
    release_manifest: Mapping[str, Any],
    redact_task_details: bool,
) -> dict[str, Any]:
    metadata = study.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("study metadata is missing")
    private = metadata.get("corpus_visibility") == "private-heldout"
    if private and not redact_task_details:
        raise ValueError("private held-out publication requires task-detail redaction")
    publication = check_publication(study, release_manifest=release_manifest)
    if publication["eligible"] is not True:
        raise ValueError(
            "publication is ineligible: " + "; ".join(publication["reasons"])
        )
    trials = study.get("trials")
    if not isinstance(trials, list):
        raise ValueError("study has no trials list")
    valid_cells = {
        (str(trial.get("run_id")), str(observation.get("task_id")))
        for trial in trials
        if isinstance(trial, Mapping)
        and trial.get("measurement_status") == "valid"
        and isinstance(trial.get("observations"), list)
        for observation in trial["observations"]
        if isinstance(observation, Mapping)
        and observation.get("measurement_status") == "valid"
    }
    unique_task_ids = {task_id for _, task_id in valid_cells}
    task_count = len(unique_task_ids)
    valid_observation_count = len(valid_cells)
    sufficient = (
        isinstance(task_count, int)
        and task_count >= MINIMUM_PUBLICATION_TASKS
        and valid_observation_count >= MINIMUM_PUBLICATION_OBSERVATIONS
    )
    bundle: dict[str, Any] = {
        "schema_version": 1,
        "corpus": {
            "id": metadata.get("corpus_id"),
            "version": metadata.get("corpus_version"),
            "digest": metadata.get("corpus_digest"),
            "visibility": metadata.get("corpus_visibility"),
        },
        "configuration": {
            "id": metadata.get("configuration_id"),
            "protocol_id": metadata.get("protocol_id"),
            "protocol_schema_version": metadata.get("protocol_schema_version"),
            "model_identity_evidence": metadata.get("model_identity_evidence"),
        },
        "methods": {
            "report_schema_version": release_manifest.get("reporting", {}).get(
                "report_schema_version", REPORT_SCHEMA_VERSION
            ),
            "fixed_corpus_method_version": FIXED_CORPUS_METHOD_VERSION,
            "wilson_method_version": WILSON_METHOD_VERSION,
            "resampling_method_version": RESAMPLING_METHOD_VERSION,
        },
        "insufficient_aggregation": not sufficient,
    }
    if not release_manifest.get("task_count_restricted", private):
        bundle["activeTaskCount"] = task_count
    if not sufficient:
        return bundle

    report = build_study_report(study)
    whole = report.get("strata", {}).get("whole_corpus")
    if not isinstance(whole, Mapping):
        raise ValueError("study has no publishable whole-corpus stratum")
    bundle["wholeCorpus"] = _redacted_stratum(whole)
    bundle["invalidMeasurementCount"] = report["attempts"]["invalid_count"]
    bundle["incompleteAttemptCount"] = report["attempts"]["incomplete_count"]
    safe_strata: dict[str, dict[str, Any]] = {}
    for grouping in ("categories", "difficulties"):
        values = report["strata"].get(grouping, {})
        safe_strata[grouping] = {
            str(name): _redacted_stratum(value)
            for name, value in values.items()
            if value.get("task_count", 0) >= MINIMUM_PUBLICATION_TASKS
            and value.get("valid_observation_count", 0)
            >= MINIMUM_PUBLICATION_OBSERVATIONS
        }
    bundle["strata"] = safe_strata
    return bundle


def initialize_private_corpus(destination: Path, *, public_repo_root: Path) -> None:
    unresolved = destination if destination.is_absolute() else Path.cwd() / destination
    _reject_symlink_components(unresolved)
    target = unresolved.resolve(strict=False)
    public_root = public_repo_root.resolve()
    checkout_root = Path(__file__).resolve().parents[1]
    if _is_within(target, public_root) or _is_within(target, checkout_root):
        raise ValueError("private corpus destination must be outside the public repository")
    if target.exists() and any(target.iterdir()):
        raise ValueError("private corpus destination must be absent or empty")
    (target / "tasks").mkdir(parents=True, exist_ok=True)
    (target / "contracts").mkdir()
    (target / "corpus").mkdir()
    (target / "plans").mkdir()
    (target / ".github" / "workflows").mkdir(parents=True)
    (target / "corpus.toml").write_text(
        "schema_version = 1\n"
        'id = "replace-with-private-corpus-id"\n'
        'version = "0.1.0-dev"\n'
        'visibility = "private-heldout"\n'
    )
    (target / "corpus" / "task-lifecycle.toml").write_text(
        "schema_version = 1\nquarantined_tasks = []\n"
    )
    (target / ".gitignore").write_text(
        "results/\npublication*.json\n*.log\n# Never copy this directory into the public NixBench repository.\n"
    )
    (target / "SECURITY.md").write_text(
        "# Private corpus handling\n\n"
        "Keep active prompts, starters, references, evaluators, logs, and task IDs "
        "outside the public NixBench repository and its Git history. Do not upload "
        "release-check artifacts that contain task-level data.\n"
    )
    (target / "plans" / "001-first-heldout-release.md").write_text(
        "# First held-out release plan\n\n"
        "Do not implement tasks until an operator records all items below.\n\n"
        "- [ ] Exact task briefs and ownership\n"
        "- [ ] At least three materially different calibration configurations\n"
        "- [ ] Repetition count and cost budget\n"
        "- [ ] Objective activation and quarantine thresholds\n"
        "- [ ] Rotation date or leaderboard cycle\n"
        "- [ ] Approved linux-bwrap-v1 execution host\n"
    )
    (target / "ROTATION.md").write_text(
        "# Rotation and retirement checklist\n\n"
        "- Record the rotation reason before reviewing new comparison results.\n"
        "- Quarantine disputed tasks before changing their contracts.\n"
        "- Remove retired tasks from active scoring.\n"
        "- Publish retired prompts, references, evaluators, and history only after approval.\n"
        "- Keep historical corpus and configuration identities immutable.\n"
    )
    (target / ".github" / "workflows" / "release-check.yml").write_text(
        "name: Private corpus release check\n"
        "on: [pull_request]\n"
        "jobs:\n"
        "  release:\n"
        "    runs-on: self-hosted\n"
        "    steps:\n"
        "      - uses: actions/checkout@v6\n"
        "      - run: python3 /trusted/nixbench/bench.py release-check --corpus-root . --json\n"
        "      # Do not upload task-level artifacts or logs.\n"
    )


def collect_health_evidence(
    tasks: Sequence[Task], contracts_dir: Path
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="nixbench-release-") as temp:
        root = Path(temp)
        results_dir = root / "results"
        for task in tasks:
            reference_runs = [
                run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"release-{task.id}-reference-{index}",
                    solution_mode="reference",
                )
                for index in range(2)
            ]
            starter = run_task(
                task,
                results_dir=results_dir,
                run_id=f"release-{task.id}-starter",
                solution_mode="starter",
            )
            deterministic = _health_signature(reference_runs[0]) == _health_signature(
                reference_runs[1]
            )
            durations = [run.check.duration_seconds for run in reference_runs]
            invalid_count = sum(
                run.measurement_status != "valid" for run in reference_runs
            ) + int(starter.measurement_status != "valid")
            pass_count = 0
            reject_count = 0
            known_issue_count = 0
            covered: set[str] = set()
            outcomes_match = True
            for manifest_path in sorted((contracts_dir / task.id).glob("*/case.toml")):
                with manifest_path.open("rb") as handle:
                    manifest = tomllib.load(handle)
                if manifest.get("known_issue"):
                    known_issue_count += 1
                    continue
                outcome = manifest.get("outcome")
                criterion_id = manifest.get("criterion_id")
                if outcome not in {"pass", "reject"} or not isinstance(
                    criterion_id, str
                ):
                    raise ValueError(f"invalid contract manifest: {manifest_path}")
                covered.add(criterion_id)
                pass_count += int(outcome == "pass")
                reject_count += int(outcome == "reject")
                fixture_runs = [
                    _run_contract_candidate(
                        task,
                        manifest_path.parent / "candidate",
                        results_dir,
                        root,
                        manifest_path.parent.name,
                        index,
                    )
                    for index in range(2)
                ]
                deterministic = deterministic and (
                    _health_signature(fixture_runs[0])
                    == _health_signature(fixture_runs[1])
                )
                durations.extend(run.check.duration_seconds for run in fixture_runs)
                invalid_count += sum(
                    run.measurement_status != "valid" for run in fixture_runs
                )
                outcomes_match = outcomes_match and all(
                    run.passed
                    if outcome == "pass"
                    else run.measurement_status == "valid"
                    and run.task_outcome == "fail"
                    and not run.passed
                    for run in fixture_runs
                )
            evidence.append(
                {
                    "task_id": task.id,
                    "category": task.category,
                    "difficulty": task.difficulty,
                    "reference_full_score": all(
                        run.measurement_status == "valid"
                        and run.passed
                        and run.score == run.max_score
                        for run in reference_runs
                    ),
                    "starter_rejected": starter.measurement_status == "valid"
                    and starter.task_outcome == "fail"
                    and not starter.passed,
                    "pass_fixture_count": pass_count,
                    "reject_fixture_count": reject_count,
                    "criterion_ids": [criterion.id for criterion in task.criteria],
                    "criterion_coverage": sorted(covered),
                    "evaluator_deterministic": deterministic,
                    "contract_outcomes_match": outcomes_match,
                    "invalid_measurement_count": invalid_count,
                    "evaluator_durations_seconds": durations,
                    "timeout_seconds": task.timeout_seconds,
                    "known_issue_count": known_issue_count,
                }
            )
    return evidence


def _run_contract_candidate(
    task: Task,
    candidate_dir: Path,
    results_dir: Path,
    root: Path,
    case_id: str,
    index: int,
) -> TaskRunResult:
    clone_root = root / "candidates" / task.id / case_id / str(index)
    shutil.copytree(task.root, clone_root)
    shutil.copytree(candidate_dir, clone_root / "starter", dirs_exist_ok=True)
    return run_task(
        load_task(clone_root),
        results_dir=results_dir,
        run_id=f"release-{task.id}-{case_id}-{index}",
        solution_mode="starter",
    )


def _health_signature(result: TaskRunResult) -> tuple[object, ...]:
    return (
        result.measurement_status,
        result.task_outcome,
        result.passed,
        result.score,
        result.max_score,
        tuple(sorted(result.criteria.items())),
        tuple(result.failure_classes),
        result.invalid_reason,
        result.check.returncode,
        result.check.timed_out,
    )


def _safe_corpus_identity(identity: CorpusIdentity) -> dict[str, Any]:
    result = {
        "schema_version": identity.schema_version,
        "id": identity.id,
        "version": identity.version,
        "visibility": identity.visibility,
        "digest": identity.digest,
        "task_count": identity.task_count,
    }
    if identity.visibility == "public":
        result["task_ids"] = list(identity.task_ids)
        result["task_digests"] = dict(identity.task_digests)
    else:
        result["task_ids"] = []
        result["task_digests"] = {}
        result["opaque_task_hashes"] = sorted(
            hashlib.sha256(digest.encode("ascii")).hexdigest()
            for digest in identity.task_digests.values()
        )
    return result


def _release_gate_digest(
    report: Mapping[str, Any], *, root: Path, evidence: Sequence[Mapping[str, Any]]
) -> str:
    evidence_files = [
        root / "corpus.toml",
        root / "corpus" / "category-vocabulary.toml",
        root / "corpus" / "task-deprecations.toml",
        root / "corpus" / "task-lifecycle.toml",
        root / "README.md",
        root / "docs" / "benchmark-governance.md",
        root / "docs" / "reproducibility.md",
        root / "docs" / "running-agents.md",
        root / "docs" / "authoring.md",
        root / "docs" / "benchmark-design.md",
        root / "docs" / "scoring.md",
        root / "docs" / "task-format.md",
        root / "docs" / "releases" / f"{report['corpus']['version']}.md",
        Path(__file__),
        Path(__file__).with_name("agent_status.py"),
        Path(__file__).with_name("isolation.py"),
        Path(__file__).with_name("adapters.py"),
        Path(__file__).with_name("cli.py"),
        Path(__file__).with_name("corpus.py"),
        Path(__file__).with_name("export.py"),
        Path(__file__).with_name("protocol.py"),
        Path(__file__).with_name("runner.py"),
        Path(__file__).with_name("scoring.py"),
        Path(__file__).with_name("reporting.py"),
        Path(__file__).with_name("study.py"),
        Path(__file__).with_name("task.py"),
        root / "scripts" / "bwrap-codex-agent.py",
        root / "launchers" / "linux-bwrap-v1.toml",
    ]
    payload = {
        "corpus_digest": report["corpus"]["digest"],
        "gates": [
            {"name": gate["name"], "passed": gate["passed"]}
            for gate in report["gates"]
        ],
        "health_evidence_digest": _hash_json(
            [_stable_health_evidence(item) for item in evidence]
        ),
        "evidence_digests": {
            (
                path.resolve().relative_to(root).as_posix()
                if _is_within(path.resolve(), root)
                else path.name
            ): hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file()
            else None
            for path in evidence_files
        },
        "tool_versions": report["tool_versions"],
    }
    return _hash_json(payload)


def _verify_release_manifest(
    path: Path, report: Mapping[str, Any]
) -> tuple[bool, str]:
    try:
        manifest = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "checked release manifest is missing or unreadable"
    if not isinstance(manifest, Mapping):
        return False, "checked release manifest is not a JSON object"
    required_fields = {
        "schema_version",
        "corpus_id",
        "corpus_version",
        "corpus_digest",
        "visibility",
        "release_date",
        "task_count",
        "category_counts",
        "difficulty_counts",
        "scoring_schema",
        "reporting",
        "release_gate_result_digest",
        "required_protocol_schema_version",
        "previous_version",
        "compatibility",
        "added_tasks",
        "changed_tasks",
        "deprecated_tasks",
        "task_count_restricted",
        "active_tasks",
        "task_digests",
        "trusted_isolation",
    }
    if set(manifest) != required_fields or manifest.get("schema_version") != 1:
        return False, "checked release manifest fields do not match schema 1"
    corpus = report["corpus"]
    strata = report.get("strata")
    if not isinstance(strata, Mapping):
        return False, "release report has no corpus strata"
    live_fields = {
        "corpus_id": corpus.get("id"),
        "corpus_version": corpus.get("version"),
        "corpus_digest": corpus.get("digest"),
        "visibility": corpus.get("visibility"),
        "task_count": corpus.get("task_count"),
        "category_counts": strata.get("categories"),
        "difficulty_counts": strata.get("difficulties"),
        "scoring_schema": "criteria-v2",
        "reporting": report.get("tool_versions"),
        "release_gate_result_digest": report.get("release_gate_result_digest"),
        "required_protocol_schema_version": report.get(
            "required_protocol_schema_version"
        ),
        "task_count_restricted": corpus.get("visibility") != "public",
    }
    for field, expected in live_fields.items():
        if manifest.get(field) != expected:
            label = field.replace("_", " ")
            return False, f"checked release manifest {label} does not match release evidence"
    active_tasks = (
        _string_list(corpus.get("task_ids", []))
        if corpus.get("visibility") == "public"
        else _string_list(corpus.get("opaque_task_hashes", []))
    )
    expected_task_digests = (
        dict(corpus.get("task_digests", {}))
        if corpus.get("visibility") == "public"
        else {}
    )
    if manifest.get("active_tasks") != active_tasks:
        return False, "checked release manifest active task set is stale"
    if manifest.get("task_digests") != expected_task_digests:
        return False, "checked release manifest task digests are stale"
    if corpus.get("visibility") == "private-heldout":
        isolation = manifest.get("trusted_isolation")
        if not isinstance(isolation, Mapping):
            return False, "private release manifest has no trusted isolation policy"
        adapter = get_trusted_adapter("codex-json-bwrap")
        expected_isolation = {
            "profile": APPROVED_HELDOUT_PROFILE,
            "adapter": adapter.id,
            "adapter_sha256": adapter.sha256,
            "attestation_trust": adapter.trust,
            "preflight_evidence": APPROVED_PREFLIGHT_EVIDENCE,
        }
        if isolation != expected_isolation:
            return False, "private release manifest trusted isolation policy is stale"
    elif manifest.get("trusted_isolation") is not None:
        return False, "non-held-out release manifest must not claim trusted isolation"
    changes_ok, changes_reason = _verify_task_change_claims(path, manifest)
    if not changes_ok:
        return False, changes_reason
    return True, "checked release manifest does not match release evidence"


def _runtime_has_margin(item: Mapping[str, Any]) -> bool:
    timeout = item.get("timeout_seconds")
    durations = item.get("evaluator_durations_seconds")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        return False
    if not isinstance(durations, list) or not durations:
        return False
    return all(
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and 0 <= value < float(timeout) * RUNTIME_SAFETY_FRACTION
        for value in durations
    )


def _stable_health_evidence(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_id": item.get("task_id"),
        "reference_full_score": item.get("reference_full_score") is True,
        "starter_rejected": item.get("starter_rejected") is True,
        "pass_fixture_count": int(item.get("pass_fixture_count", 0)),
        "reject_fixture_count": int(item.get("reject_fixture_count", 0)),
        "criterion_ids": sorted(_string_list(item.get("criterion_ids", []))),
        "criterion_coverage": sorted(
            _string_list(item.get("criterion_coverage", []))
        ),
        "evaluator_deterministic": item.get("evaluator_deterministic") is True,
        "contract_outcomes_match": item.get("contract_outcomes_match") is True,
        "invalid_measurement_count": int(item.get("invalid_measurement_count", 0)),
        "runtime_has_margin": _runtime_has_margin(item),
        "known_issue_count": int(item.get("known_issue_count", 0)),
    }


def _load_category_vocabulary(path: Path) -> set[str]:
    data = _load_toml(path, "category vocabulary")
    categories = data.get("categories")
    if not isinstance(categories, list) or not categories or not all(
        isinstance(item, str) and item for item in categories
    ):
        raise ValueError("category vocabulary must define a nonempty categories list")
    if len(categories) != len(set(categories)):
        raise ValueError("category vocabulary contains duplicates")
    return set(categories)


def _load_deprecations(path: Path) -> dict[str, Mapping[str, Any]]:
    data = _load_toml(path, "task deprecations")
    if data.get("schema_version") != 1:
        raise ValueError("task deprecations schema_version must be 1")
    values = data.get("deprecations")
    if not isinstance(values, list):
        raise ValueError("task deprecations must define a deprecations array")
    result: dict[str, Mapping[str, Any]] = {}
    for item in values:
        if not isinstance(item, Mapping) or not isinstance(item.get("task_id"), str):
            raise ValueError("each task deprecation must contain a task_id")
        result[str(item["task_id"])] = item
    return result


def _load_quarantined_tasks(path: Path) -> set[str]:
    data = _load_toml(path, "task lifecycle policy")
    if data.get("schema_version") != 1:
        raise ValueError("task lifecycle schema_version must be 1")
    expected = {"schema_version", "quarantined_tasks"}
    if set(data) != expected:
        raise ValueError("task lifecycle fields do not match schema 1")
    return set(_string_list(data.get("quarantined_tasks")))


def _load_toml(path: Path, label: str) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            value = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    return value


def _redacted_stratum(value: Mapping[str, Any]) -> dict[str, Any]:
    scalar_allowed = (
        "task_count",
        "valid_observation_count",
        "trial_count",
        "complete_trial_count",
        "macro_task_score",
        "macro_pass_rate",
        "point_weighted_score",
        "raw_points",
        "normalized_score_range",
        "timeout_count",
        "timeout_rate",
        "descriptive_only",
        "status",
    )
    result = {key: value.get(key) for key in scalar_allowed}
    result["raw_points"] = _safe_scalar_mapping(
        value.get("raw_points"), allowed={"earned", "available"}
    )
    result["normalized_score_range"] = _safe_scalar_mapping(
        value.get("normalized_score_range"), allowed={"min", "max"}
    )
    for key in ("run_variation", "resampling_sensitivity"):
        result[key] = _redacted_method(value.get(key))
    return result


def _redacted_method(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    scalar_fields = (
        "method",
        "method_version",
        "sampling_unit",
        "n",
        "estimate",
        "standard_deviation",
        "replicates",
        "unavailable_reason",
    )
    result = {key: value.get(key) for key in scalar_fields}
    result["interval"] = _safe_scalar_mapping(
        value.get("interval"),
        allowed={
            "level",
            "margin",
            "raw_low",
            "raw_high",
            "display_low",
            "display_high",
            "low",
            "high",
        },
    )
    result["range"] = _safe_scalar_mapping(
        value.get("range"), allowed={"min", "max"}
    )
    return result


def _safe_scalar_mapping(
    value: object, *, allowed: set[str]
) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(key, str)
        and key in allowed
        and (item is None or type(item) in {bool, int, float, str})
    }


def _verify_task_change_claims(
    manifest_path: Path, manifest: Mapping[str, Any]
) -> tuple[bool, str]:
    try:
        active = set(_string_list(manifest.get("active_tasks")))
        added = set(_string_list(manifest.get("added_tasks")))
        changed = set(_string_list(manifest.get("changed_tasks")))
        deprecated = set(_string_list(manifest.get("deprecated_tasks")))
    except ValueError:
        return False, "checked release manifest task-change fields are invalid"
    if len(active) != len(manifest.get("active_tasks", [])):
        return False, "checked release manifest active task set contains duplicates"
    previous_version = manifest.get("previous_version")
    if previous_version is None:
        if added != active or changed or deprecated:
            return False, "initial release task-change classification is not truthful"
        return True, ""
    if not isinstance(previous_version, str) or not previous_version:
        return False, "checked release manifest previous_version is invalid"
    previous_path = manifest_path.with_name(f"{previous_version}.json")
    try:
        previous = json.loads(previous_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False, "previous release manifest is missing or unreadable"
    if not isinstance(previous, Mapping):
        return False, "previous release manifest is invalid"
    try:
        previous_active = set(_string_list(previous.get("active_tasks")))
    except ValueError:
        return False, "previous release manifest active task set is invalid"
    current_digests = manifest.get("task_digests")
    previous_digests = previous.get("task_digests")
    if not isinstance(current_digests, Mapping) or not isinstance(
        previous_digests, Mapping
    ):
        return False, "release manifest task digest maps are invalid"
    expected_added = active - previous_active
    expected_deprecated = previous_active - active
    expected_changed = {
        task_id
        for task_id in active & previous_active
        if current_digests.get(task_id) != previous_digests.get(task_id)
    }
    if (
        added != expected_added
        or changed != expected_changed
        or deprecated != expected_deprecated
    ):
        return False, "release task-change classification is not truthful"
    if manifest.get("visibility") == "public" and deprecated:
        try:
            recorded = set(
                _load_deprecations(
                    manifest_path.parent.parent / "task-deprecations.toml"
                )
            )
        except ValueError:
            return False, "task deprecation registry is missing or invalid"
        if not deprecated <= recorded:
            return False, "release manifest has unrecorded deprecated tasks"
    return True, ""


def _reject_symlink_components(path: Path) -> None:
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise ValueError("private corpus destination must not contain symlink components")
        if not current.exists():
            break


def _tool_versions() -> dict[str, int | str]:
    return {
        "release_tool_schema_version": RELEASE_TOOL_SCHEMA_VERSION,
        "report_schema_version": REPORT_SCHEMA_VERSION,
        "corpus_health_schema_version": CORPUS_HEALTH_SCHEMA_VERSION,
        "fixed_corpus_method_version": FIXED_CORPUS_METHOD_VERSION,
        "wilson_method_version": WILSON_METHOD_VERSION,
        "resampling_method_version": RESAMPLING_METHOD_VERSION,
    }


def _add_gate(
    gates: list[dict[str, Any]],
    name: str,
    passed: bool,
    success_reason: str,
    failure_reason: str,
) -> None:
    gates.append(
        {
            "name": name,
            "passed": bool(passed),
            "reason": success_reason if passed else failure_reason,
        }
    )


def _hash_json(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError("expected a list of strings")
    return list(value)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
