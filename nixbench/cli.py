from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .corpus import CorpusIdentity, identify_corpus
from .export import export_studies_for_site
from .isolation import APPROVED_PREFLIGHT_EVIDENCE
from .protocol import ResolvedProtocol, resolve_protocol
from .reporting import (
    build_corpus_health_report,
    build_study_report,
    load_study_summary,
)
from .release import (
    check_publication,
    check_release,
    export_publication_bundle,
    health_report_provenance,
    initialize_private_corpus,
    load_verified_health_evidence,
)
from .runner import TaskRunResult, SolutionMode, detect_nix_system, make_run_id, run_task, write_summary
from .study import (
    build_study_attempt,
    build_study_trial,
    count_study_trials,
    write_study_summary,
)
from .task import Task, TaskError, find_task, iter_tasks, load_task

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib  # type: ignore[no-redef]


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

    corpus_parser = subparsers.add_parser(
        "corpus-id", help="Print the content-addressed corpus identity."
    )
    corpus_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    corpus_parser.set_defaults(func=cmd_corpus_id)

    report_parser = subparsers.add_parser(
        "report-study", help="Build canonical statistics from a study summary."
    )
    report_parser.add_argument("--study-path", type=Path, required=True)
    report_parser.add_argument("--json", action="store_true", help="Emit JSON.")
    report_parser.set_defaults(func=cmd_report_study)

    health_parser = subparsers.add_parser(
        "corpus-health", help="Evaluate corpus checks and write a health report."
    )
    health_parser.add_argument("--studies-dir", type=Path, required=True)
    health_parser.add_argument("--contracts-dir", type=Path, default=Path("contracts"))
    health_parser.add_argument("--output", type=Path, required=True)
    health_parser.set_defaults(func=cmd_corpus_health)

    release_parser = subparsers.add_parser(
        "release-check", help="Evaluate corpus release eligibility."
    )
    release_parser.add_argument("--corpus-root", type=Path, required=True)
    release_parser.add_argument("--health-report", type=Path)
    release_parser.add_argument("--json", action="store_true")
    release_parser.add_argument("--explain", action="store_true")
    release_parser.set_defaults(func=cmd_release_check)

    publication_parser = subparsers.add_parser(
        "publication-check", help="Evaluate whether a study may be published."
    )
    publication_parser.add_argument("--study-path", type=Path, required=True)
    publication_parser.add_argument("--release-manifest", type=Path, required=True)
    publication_parser.add_argument("--json", action="store_true")
    publication_parser.set_defaults(func=cmd_publication_check)

    publication_export = subparsers.add_parser(
        "export-publication", help="Write a disclosure-safe publication bundle."
    )
    publication_export.add_argument("--study-path", type=Path, required=True)
    publication_export.add_argument("--release-manifest", type=Path, required=True)
    publication_export.add_argument("--redact-task-details", action="store_true")
    publication_export.add_argument("--output", type=Path, required=True)
    publication_export.set_defaults(func=cmd_export_publication)

    private_parser = subparsers.add_parser(
        "init-private-corpus", help="Create an empty local held-out corpus template."
    )
    private_parser.add_argument("--destination", type=Path, required=True)
    private_parser.add_argument("--public-repo-root", type=Path, default=Path("."))
    private_parser.set_defaults(func=cmd_init_private_corpus)

    run_parser = subparsers.add_parser("run", help="Run one benchmark task.")
    run_parser.add_argument("task_id", help="Task id or directory name.")
    add_run_options(run_parser)
    run_parser.set_defaults(func=cmd_run)

    run_all_parser = subparsers.add_parser("run-all", help="Run all benchmark tasks for the selected system.")
    add_run_options(run_all_parser)
    run_all_parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Repeat the full corpus this many times and write an uncertainty-aware study summary.",
    )
    run_all_parser.add_argument("--model", help="Model identifier recorded in the study metadata.")
    run_all_parser.add_argument("--effort", help="Reasoning-effort label recorded in the study metadata.")
    run_all_parser.add_argument("--series", help="Stable site series key recorded in the study metadata.")
    run_all_parser.add_argument("--marker", help="Short chart marker recorded in the study metadata.")
    run_all_parser.add_argument(
        "--kind",
        choices=["codex", "claude", "opencode", "pi"],
        help="Agent kind recorded in the study metadata.",
    )
    run_all_parser.add_argument("--label", help="Human-readable agent label recorded in the study metadata.")
    run_all_parser.add_argument("--agent-version", help="Agent version recorded in the study metadata.")
    run_all_parser.add_argument(
        "--network",
        choices=["enabled", "disabled", "unknown"],
        help="Agent network-access state recorded in the study metadata.",
    )
    run_all_parser.set_defaults(func=cmd_run_all)

    export_parser = subparsers.add_parser(
        "export-site",
        help="Export recorded study trials as checked site data.",
    )
    export_parser.add_argument("--output", type=Path, required=True, help="Destination JSON file.")
    export_parser.add_argument("--task-count", type=int, help="Only export studies with this corpus size.")
    export_parser.add_argument("--minimum-trials", type=int, default=1)
    export_parser.add_argument("--expected-configurations", type=int)
    export_parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge exported trials into an existing output file by row ID.",
    )
    export_parser.add_argument(
        "--allow-legacy-protocol",
        action="store_true",
        help="Allow explicitly requested export of old studies without protocol identity.",
    )
    export_parser.set_defaults(func=cmd_export_site)

    count_parser = subparsers.add_parser(
        "study-count",
        help="Print the number of completed study trials for one configuration.",
    )
    count_parser.add_argument("--configuration-id")
    count_parser.add_argument("--corpus-digest")
    count_parser.add_argument("--protocol-file", type=Path)
    count_parser.add_argument("--wrapper-prompt-file", type=Path)
    count_parser.add_argument("--agent-cmd")
    count_parser.add_argument("--agent-adapter")
    count_parser.add_argument("--agent-timeout-seconds", type=int, default=300)
    count_parser.add_argument("--series", help="Deprecated display-only selector.")
    count_parser.add_argument("--effort", help="Deprecated display-only selector.")
    count_parser.add_argument("--task-count", type=int, help="Deprecated corpus-size selector.")
    count_parser.set_defaults(func=cmd_study_count)

    validate_parser = subparsers.add_parser("validate", help="Run task evaluators against starter or reference solutions.")
    validate_parser.add_argument("--solution", choices=["starter", "reference"], default="reference")
    validate_parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary work directories.")
    validate_parser.set_defaults(func=cmd_validate)

    return parser


def add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--agent-cmd", help="Shell command that edits the copied task workdir.")
    parser.add_argument(
        "--agent-adapter",
        help="Registered trusted adapter used to launch and attest the agent command.",
    )
    parser.add_argument(
        "--solution",
        choices=["agent", "starter", "reference"],
        default="agent",
        help="What to evaluate: an agent run, the starter files, or the reference solution.",
    )
    parser.add_argument("--agent-timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--protocol-file", type=Path, help="Controlled run protocol TOML."
    )
    parser.add_argument(
        "--wrapper-prompt-file",
        type=Path,
        help="Exact wrapper prompt whose bytes are part of the protocol identity.",
    )
    parser.add_argument("--keep-workdir", action="store_true", help="Keep temporary work directories.")


def cmd_corpus_id(args: argparse.Namespace) -> int:
    identity = identify_corpus(args.tasks_dir)
    if args.json:
        print(json.dumps(identity.to_json(), indent=2, sort_keys=True))
        return 0
    print(f"id: {identity.id}")
    print(f"version: {identity.version}")
    print(f"visibility: {identity.visibility}")
    print(f"digest: {identity.digest}")
    print(f"task_count: {identity.task_count}")
    return 0


def cmd_report_study(args: argparse.Namespace) -> int:
    study = load_study_summary(args.study_path)
    report = build_study_report(study)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    else:
        print(f"study: {report.get('study_id')}")
        print(f"aggregate_only: {str(report['aggregate_only']).lower()}")
        whole = report.get("strata", {}).get("whole_corpus") if report.get("strata") else None
        if whole is not None:
            print(f"trials: {whole['trial_count']}")
            print(f"tasks: {whole['task_count']}")
            print(f"macro_task_score: {whole['macro_task_score']:.6f}")
    return 0


def cmd_corpus_health(args: argparse.Namespace) -> int:
    corpus = identify_corpus(args.tasks_dir)
    tasks = [task for task in iter_tasks(args.tasks_dir) if task.supports_system(args.system)]
    if not tasks:
        raise ValueError(f"no tasks in {args.tasks_dir} support system {args.system}")
    evidence = _collect_corpus_health_evidence(tasks, args.contracts_dir)
    studies = [
        load_study_summary(path)
        for path in sorted(args.studies_dir.glob("*/summary.json"))
    ]
    report = build_corpus_health_report(
        corpus_digest=corpus.digest,
        task_evidence=evidence,
        studies=studies,
    )
    payload = {
        "schema_version": 1,
        "corpora": {corpus.digest: report},
        "release_provenance": health_report_provenance(corpus.digest, evidence),
        "release_evidence": evidence,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(f"wrote corpus health for {len(tasks)} tasks to {args.output}")
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    evidence = (
        load_verified_health_evidence(
            args.health_report, corpus_root=args.corpus_root.resolve()
        )
        if args.health_report is not None
        else None
    )
    report = check_release(
        args.corpus_root,
        health_evidence=evidence,
        system=args.system,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    else:
        status = "eligible" if report["eligible"] else "ineligible"
        print(f"release: {status}")
        for gate in report["gates"]:
            marker = "PASS" if gate["passed"] else "FAIL"
            print(f"{marker} {gate['name']}: {gate['reason']}")
        if args.explain:
            print("policy: docs/benchmark-governance.md")
            print("categories: corpus/category-vocabulary.toml")
            print("deprecations: corpus/task-deprecations.toml")
    return 0 if report["eligible"] else 1


def cmd_publication_check(args: argparse.Namespace) -> int:
    study = _load_json_object(args.study_path, "study")
    manifest = _load_json_object(args.release_manifest, "release manifest")
    report = check_publication(study, release_manifest=manifest)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("publication: " + ("eligible" if report["eligible"] else "ineligible"))
        for reason in report["reasons"]:
            print(f"- {reason}")
    return 0 if report["eligible"] else 1


def cmd_export_publication(args: argparse.Namespace) -> int:
    study = _load_json_object(args.study_path, "study")
    manifest = _load_json_object(args.release_manifest, "release manifest")
    bundle = export_publication_bundle(
        study,
        release_manifest=manifest,
        redact_task_details=args.redact_task_details,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(f"wrote publication bundle to {args.output}")
    return 0


def cmd_init_private_corpus(args: argparse.Namespace) -> int:
    initialize_private_corpus(
        args.destination, public_repo_root=args.public_repo_root
    )
    print(f"created private corpus template at {args.destination}")
    return 0


def _load_json_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _collect_corpus_health_evidence(
    tasks: list[Task], contracts_dir: Path
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="nixbench-health-") as temp:
        root = Path(temp)
        results_dir = root / "results"
        for task in tasks:
            reference_runs = [
                run_task(
                    task,
                    results_dir=results_dir,
                    run_id=f"health-{task.id}-reference-{index}",
                    solution_mode="reference",
                )
                for index in range(2)
            ]
            starter = run_task(
                task,
                results_dir=results_dir,
                run_id=f"health-{task.id}-starter",
                solution_mode="starter",
            )
            deterministic = _health_signature(reference_runs[0]) == _health_signature(
                reference_runs[1]
            )
            durations = [run.check.duration_seconds for run in reference_runs]
            invalid_measurement_count = sum(
                run.measurement_status != "valid" for run in reference_runs
            ) + int(starter.measurement_status != "valid")
            pass_count = 0
            reject_count = 0
            known_issue_count = 0
            covered: set[str] = set()
            contract_outcomes_match = True
            task_contracts = contracts_dir / task.id
            for manifest_path in sorted(task_contracts.glob("*/case.toml")):
                with manifest_path.open("rb") as handle:
                    manifest = tomllib.load(handle)
                if manifest.get("known_issue"):
                    known_issue_count += 1
                    continue
                outcome = manifest.get("outcome")
                criterion_id = manifest.get("criterion_id")
                if outcome not in {"pass", "reject"}:
                    raise ValueError(f"{manifest_path}: invalid outcome")
                if not isinstance(criterion_id, str) or not criterion_id:
                    raise ValueError(f"{manifest_path}: missing criterion_id")
                covered.add(criterion_id)
                if outcome == "pass":
                    pass_count += 1
                else:
                    reject_count += 1
                fixture_runs = [
                    _run_health_contract_candidate(
                        task,
                        manifest_path.parent / "candidate",
                        results_dir=results_dir,
                        root=root,
                        case_id=manifest_path.parent.name,
                        index=index,
                    )
                    for index in range(2)
                ]
                deterministic = deterministic and (
                    _health_signature(fixture_runs[0])
                    == _health_signature(fixture_runs[1])
                )
                durations.extend(run.check.duration_seconds for run in fixture_runs)
                invalid_measurement_count += sum(
                    run.measurement_status != "valid" for run in fixture_runs
                )
                for run in fixture_runs:
                    expected = run.passed if outcome == "pass" else (
                        run.measurement_status == "valid"
                        and run.task_outcome == "fail"
                        and not run.passed
                    )
                    contract_outcomes_match = contract_outcomes_match and expected
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
                    "starter_rejected": (
                        starter.measurement_status == "valid"
                        and starter.task_outcome == "fail"
                        and not starter.passed
                    ),
                    "pass_fixture_count": pass_count,
                    "reject_fixture_count": reject_count,
                    "criterion_ids": [criterion.id for criterion in task.criteria],
                    "criterion_coverage": sorted(covered),
                    "evaluator_deterministic": deterministic,
                    "contract_outcomes_match": contract_outcomes_match,
                    "evaluator_durations_seconds": durations,
                    "invalid_measurement_count": invalid_measurement_count,
                    "timeout_seconds": task.timeout_seconds,
                    "known_issue_count": known_issue_count,
                }
            )
    return evidence


def _run_health_contract_candidate(
    task: Task,
    candidate_dir: Path,
    *,
    results_dir: Path,
    root: Path,
    case_id: str,
    index: int,
) -> TaskRunResult:
    if not candidate_dir.is_dir():
        raise ValueError(f"missing contract candidate directory: {candidate_dir}")
    clone_root = root / "candidates" / task.id / case_id / str(index)
    shutil.copytree(task.root, clone_root)
    shutil.copytree(candidate_dir, clone_root / "starter", dirs_exist_ok=True)
    candidate_task = load_task(clone_root)
    return run_task(
        candidate_task,
        results_dir=results_dir,
        run_id=f"health-{task.id}-{case_id}-{index}",
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
    corpus, protocol, metadata = _run_identity_metadata(args)
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
        completion_attestation=protocol.completion_attestation,
        agent_adapter=protocol.agent_adapter,
        wrapper_prompt_path=args.wrapper_prompt_file,
        isolation_profile=protocol.isolation_profile,
        network_policy=protocol.network_policy,
        corpus_root=args.tasks_dir.parent,
    )
    _record_isolation_metadata(metadata, protocol, [result])
    write_summary(args.results_dir, run_id, [result], metadata=metadata)
    _print_result(result)
    return 0 if result.passed else 1


def cmd_run_all(args: argparse.Namespace) -> int:
    tasks = _tasks_for_execution(args)
    if args.trials < 1:
        raise ValueError("--trials must be at least 1")

    study_id = make_run_id()
    study_trials = []
    study_attempts = []
    all_results: list[TaskRunResult] = []
    corpus, protocol, identity_metadata = _run_identity_metadata(args)
    metadata = dict(identity_metadata)
    metadata.update(
        {
            key: value
        for key, value in {
            "label": args.label,
            "model": args.model,
            "effort": args.effort,
            "series": args.series,
            "marker": args.marker,
            "kind": args.kind,
            "agent_version": args.agent_version,
            "network": args.network,
            "solution": args.solution,
            "system": args.system,
            "host": platform.node(),
            "platform": platform.platform(),
        }.items()
        if value is not None
        }
    )

    for trial_number in range(1, args.trials + 1):
        run_id = make_run_id()
        print(f"trial {trial_number}/{args.trials}: run_id={run_id}")
        results = []
        invalid_message = None
        attempt_error: BaseException | None = None
        for task in tasks:
            try:
                result = run_task(
                    task,
                    results_dir=args.results_dir,
                    run_id=run_id,
                    solution_mode=_solution_mode(args.solution),
                    agent_cmd=args.agent_cmd,
                    agent_timeout_seconds=args.agent_timeout_seconds,
                    keep_workdir=args.keep_workdir,
                    completion_attestation=protocol.completion_attestation,
                    agent_adapter=protocol.agent_adapter,
                    wrapper_prompt_path=args.wrapper_prompt_file,
                    isolation_profile=protocol.isolation_profile,
                    network_policy=protocol.network_policy,
                    corpus_root=args.tasks_dir.parent,
                )
            except BaseException as exc:
                attempt_error = exc
                break
            results.append(result)
            _print_result(result)
            if result.measurement_status == "invalid":
                invalid_message = (
                    f"trial {trial_number} is invalid on {result.task_id}: "
                    f"{result.invalid_reason}"
                )
                break

        summary_path = write_summary(
            args.results_dir,
            run_id,
            results,
            metadata={**metadata, "study_id": study_id, "trial": trial_number},
        )
        passed = sum(1 for result in results if result.passed)
        print(f"summary: {passed}/{len(results)} passed, wrote {summary_path}")
        attempt = build_study_attempt(
            run_id,
            results,
            expected_task_count=len(tasks),
            corpus_digest=corpus.digest,
            configuration_id=protocol.configuration_id,
            task_digests=corpus.task_digests,
            additional_exclusion_reasons=(
                ("interrupted",)
                if isinstance(attempt_error, KeyboardInterrupt)
                else (("harness-exception",) if attempt_error is not None else ())
            ),
        )
        study_attempts.append(attempt)
        if attempt["included_in_trials"]:
            study_trials.append(
                build_study_trial(
                    run_id,
                    results,
                    corpus_digest=corpus.digest,
                    configuration_id=protocol.configuration_id,
                    task_digests=corpus.task_digests,
                )
            )
        all_results.extend(results)
        _record_isolation_metadata(metadata, protocol, all_results)
        study_path = write_study_summary(
            args.results_dir,
            study_id,
            study_trials,
            metadata=metadata,
            attempts=study_attempts,
            task_count=len(tasks),
        )
        print(
            f"study checkpoint: {len(study_trials)}/{args.trials} trials, "
            f"{len(study_attempts)} attempts, wrote {study_path}"
        )
        if invalid_message is not None:
            raise ValueError(f"{invalid_message}; checkpointed before stopping")
        if attempt_error is not None:
            if isinstance(attempt_error, KeyboardInterrupt):
                raise attempt_error
            raise ValueError(
                f"trial {trial_number} stopped on a harness exception; "
                "checkpointed before stopping"
            ) from attempt_error

    print(f"study: {len(study_trials)} trials, wrote {study_path}")
    return 0 if all(result.passed for result in all_results) else 1


def cmd_export_site(args: argparse.Namespace) -> int:
    row_count = export_studies_for_site(
        args.results_dir,
        args.output,
        task_count=args.task_count,
        minimum_trials=args.minimum_trials,
        expected_configurations=args.expected_configurations,
        merge_existing=args.merge_existing,
        allow_legacy_protocol=args.allow_legacy_protocol,
    )
    print(f"exported {row_count} trial rows to {args.output}")
    return 0


def cmd_study_count(args: argparse.Namespace) -> int:
    if args.task_count is not None and args.task_count < 1:
        raise ValueError("--task-count must be at least 1")
    configuration_id = args.configuration_id
    corpus_digest = args.corpus_digest
    if args.protocol_file is not None:
        if configuration_id is not None or corpus_digest is not None:
            raise ValueError(
                "use --protocol-file or explicit identity fields, not both"
            )
        corpus, protocol, _ = _run_identity_metadata(args)
        configuration_id = protocol.configuration_id
        corpus_digest = corpus.digest
    print(
        count_study_trials(
            args.results_dir,
            configuration_id=configuration_id,
            corpus_digest=corpus_digest,
            series=args.series,
            effort=args.effort,
            task_count=args.task_count,
        )
    )
    return 0


def _git_revision(path: Path) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    revision = completed.stdout.strip()
    return revision if completed.returncode == 0 and revision else None


def _run_identity_metadata(
    args: argparse.Namespace,
) -> tuple[CorpusIdentity, ResolvedProtocol, dict[str, object]]:
    corpus = identify_corpus(args.tasks_dir)
    host = platform.node()
    platform_name = platform.platform()
    legacy_metadata = {
        key: getattr(args, key, None) for key in ("model", "effort", "network")
    }
    protocol = resolve_protocol(
        args.protocol_file,
        corpus_digest=corpus.digest,
        agent_command=args.agent_cmd,
        agent_adapter=getattr(args, "agent_adapter", None),
        wrapper_prompt_path=args.wrapper_prompt_file,
        agent_timeout_seconds=args.agent_timeout_seconds,
        system=args.system,
        host=host,
        platform=platform_name,
        legacy_metadata=legacy_metadata,
    )
    metadata: dict[str, object] = {
        "corpus_revision": _git_revision(args.tasks_dir),
        "corpus_id": corpus.id,
        "corpus_version": corpus.version,
        "corpus_visibility": corpus.visibility,
        "corpus_digest": corpus.digest,
        "corpus_task_digests": corpus.task_digests,
        "protocol": protocol.to_json(),
        "protocol_id": protocol.id,
        "protocol_schema_version": protocol.schema_version,
        "protocol_complete": protocol.protocol_complete,
        "completion_attestation": protocol.completion_attestation,
        "agent_adapter": protocol.agent_adapter,
        "agent_adapter_sha256": protocol.agent_adapter_sha256,
        "agent_adapter_bundle_sha256": protocol.agent_adapter_bundle_sha256,
        "attestation_trust": protocol.attestation_trust,
        "model_identity_evidence": protocol.model_identity_evidence,
        "wrapper_prompt_sha256": protocol.wrapper_prompt_sha256,
        "agent_command_sha256": protocol.agent_command_sha256,
        "configuration_id": protocol.configuration_id,
        "timing_environment_id": protocol.timing_environment_id,
        "host": host,
        "platform": platform_name,
        "system": args.system,
        "agent_timeout_seconds": args.agent_timeout_seconds,
        "isolation_profile": protocol.isolation_profile,
    }
    if protocol.protocol_complete:
        metadata.update(
            {
                "model": protocol.model_id,
                "effort": protocol.effort,
                "network": protocol.network_policy,
            }
        )
    return corpus, protocol, metadata


def _record_isolation_metadata(
    metadata: dict[str, object],
    protocol: ResolvedProtocol,
    results: list[TaskRunResult],
) -> None:
    if protocol.isolation_profile != "linux-bwrap-v1":
        return
    evidence = [
        result.agent_status.get("preflight_evidence")
        for result in results
        if isinstance(result.agent_status, dict)
    ]
    expected = APPROVED_PREFLIGHT_EVIDENCE
    successful = bool(results) and len(evidence) == len(results) and all(
        value == expected for value in evidence
    )
    metadata["isolation_preflight"] = {
        "successful": successful,
        "namespace_allowlist": successful,
        "workspace_writable": successful,
        "nix_daemon_absent": successful,
        "evidence": expected if successful else None,
    }


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
        return (
            result.measurement_status == "valid"
            and result.task_outcome == "pass"
            and result.passed
            and result.score == result.max_score
            and all(result.criteria.values())
        )
    return (
        result.measurement_status == "valid"
        and result.task_outcome == "fail"
        and not result.passed
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
