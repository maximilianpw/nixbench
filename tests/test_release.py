from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nixbench.isolation import (
    APPROVED_PREFLIGHT_EVIDENCE,
    build_bubblewrap_command,
    run_isolation_probe,
)
from nixbench.adapters import get_trusted_adapter
from nixbench.release import (
    build_release_manifest,
    check_publication,
    check_release,
    export_publication_bundle,
    initialize_private_corpus,
    health_report_provenance,
    load_verified_health_evidence,
)
from nixbench.runner import run_task
from nixbench.task import load_task


class ReleaseTests(unittest.TestCase):
    def test_invalid_corpus_identity_returns_a_safe_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "corpus.toml").write_text("not valid toml = [\n")

            report = check_release(root, verify_manifest=False)

            self.assertFalse(report["eligible"])
            self.assertIsNone(report["corpus"])
            self.assertEqual(report["gates"][0]["name"], "valid-corpus-identity")
            self.assertNotIn(str(root), json.dumps(report))

    def test_cached_health_requires_current_provenance_and_is_forbidden_in_ci(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_corpus(root)
            provisional = check_release(
                root,
                health_evidence=[self.healthy_evidence()],
                verify_manifest=False,
            )
            report_path = root / "health.json"
            report_path.write_text(
                json.dumps(
                    {
                        "release_provenance": health_report_provenance(
                            provisional["corpus"]["digest"],
                            [self.healthy_evidence()],
                        ),
                        "release_evidence": [self.healthy_evidence()],
                    }
                )
            )

            loaded = load_verified_health_evidence(report_path, corpus_root=root)
            self.assertEqual(loaded[0]["task_id"], "task-a")

            payload = json.loads(report_path.read_text())
            payload["release_provenance"]["release_tool_sha256"] = "0" * 64
            report_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "stale or unverifiable"):
                load_verified_health_evidence(report_path, corpus_root=root)

            payload = json.loads(report_path.read_text())
            payload["release_provenance"] = health_report_provenance(
                provisional["corpus"]["digest"], [self.healthy_evidence()]
            )
            payload["release_evidence"][0]["reference_full_score"] = False
            report_path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "stale or unverifiable"):
                load_verified_health_evidence(report_path, corpus_root=root)

            with patch.dict(os.environ, {"CI": "true"}):
                with self.assertRaisesRegex(ValueError, "forbidden in release CI"):
                    load_verified_health_evidence(report_path, corpus_root=root)

    def test_each_health_release_gate_reports_its_own_failure(self) -> None:
        cases = (
            ("complete-health-evidence", None),
            ("reference-and-starter-outcomes", ("reference_full_score", False)),
            ("independent-contract-fixtures", ("pass_fixture_count", 0)),
            ("required-rubric-coverage", ("criterion_coverage", [])),
            ("deterministic-evaluators", ("evaluator_deterministic", False)),
            ("valid-health-measurements", ("invalid_measurement_count", 1)),
            ("evaluator-runtime-margin", ("evaluator_durations_seconds", [9.0])),
            ("no-active-known-issue-skips", ("known_issue_count", 1)),
        )
        for gate_name, mutation in cases:
            with self.subTest(gate=gate_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.make_corpus(root)
                evidence = [] if mutation is None else [self.healthy_evidence()]
                if mutation is not None:
                    evidence[0][mutation[0]] = mutation[1]

                report = check_release(
                    root, health_evidence=evidence, verify_manifest=False
                )
                gates = {gate["name"]: gate for gate in report["gates"]}

                self.assertFalse(gates[gate_name]["passed"], gates[gate_name])
                self.assertFalse(report["eligible"])

    def test_trusted_bwrap_adapter_attests_and_keeps_status_outside_sandbox(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="nixbench-isolated-", dir="/tmp"
        ) as temp, tempfile.TemporaryDirectory(
            prefix="private-home-sentinel-", dir="/tmp"
        ) as host_temp:
            root = Path(temp)
            host_root = Path(host_temp)
            workspace = root / "work"
            workspace.mkdir()
            forbidden = host_root / "corpus" / "sentinel"
            forbidden.parent.mkdir()
            forbidden.write_text("secret")
            host_sentinel = "/host/private/NIXBENCH-FORBIDDEN-SENTINEL"
            fake_agent = host_root / "home" / "tools" / "fake-agent"
            fake_agent.parent.mkdir(parents=True)
            fake_agent.write_text(
                "#!/bin/sh\n"
                f"test ! -e {forbidden}\n"
                "test -z \"${NIXBENCH_AGENT_STATUS_FILE:-}\"\n"
                "while IFS= read -r -d '' value; do "
                "printf '%s\\0' \"$value\"; done < /proc/1/cmdline > proc-cmdline\n"
                "while IFS= read -r -d '' value; do "
                "printf '%s\\0' \"$value\"; done < /proc/1/environ > proc-environ\n"
                "while IFS= read -r line; do printf '%s\\n' \"$line\"; "
                "done < /proc/self/mountinfo > mountinfo.txt\n"
                "printf edited > answer.txt\n"
                "printf '%s\\n' '{\"type\":\"thread.started\"}' "
                "'{\"type\":\"turn.completed\"}'\n"
            )
            fake_agent.chmod(0o755)
            status = root / "attestation" / "status.json"
            status.parent.mkdir()
            adapter = get_trusted_adapter("codex-json-bwrap")
            command = adapter.command(
                f"{fake_agent} --json",
                workspace=workspace,
                forbidden_paths=[forbidden, Path(host_sentinel)],
                network_policy="enabled",
            )
            self.assertNotIn(host_sentinel, " ".join(command))
            env = os.environ.copy()
            env["NIXBENCH_AGENT_STATUS_FILE"] = str(status)
            env["PATH"] = f"{host_sentinel}:{env['PATH']}"

            completed = subprocess.run(
                command,
                cwd=workspace,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(status.read_text())
            self.assertTrue(payload["preflight"]["successful"])
            self.assertIn("linux-bwrap-v1", payload["preflight"]["evidence"])
            self.assertTrue(payload["completed"])
            self.assertEqual((workspace / "answer.txt").read_text(), "edited")
            self.assertGreater((workspace / "proc-cmdline").stat().st_size, 0)
            self.assertGreater((workspace / "proc-environ").stat().st_size, 0)
            proc_cmdline = (workspace / "proc-cmdline").read_bytes()
            proc_environ = (workspace / "proc-environ").read_bytes()
            mountinfo = (workspace / "mountinfo.txt").read_text()
            self.assertNotIn(host_sentinel.encode(), proc_cmdline)
            self.assertNotIn(host_sentinel.encode(), proc_environ)
            self.assertNotIn(str(root).encode(), proc_cmdline)
            self.assertNotIn(str(root).encode(), proc_environ)
            self.assertNotIn(str(host_root), mountinfo)
            self.assertNotIn(str(fake_agent), mountinfo)
            self.assertIn(b"PATH=/run/nixbench:/usr/bin:/bin\0", proc_environ)
            self.assertIn(b"HOME=/home/agent\0", proc_environ)
            self.assertNotIn(b"NIXBENCH_AGENT_STATUS_FILE=", proc_environ)

    def test_runner_uses_isolation_then_runs_hidden_evaluator_on_host(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_id = "private-heldout-task-sentinel"
            task_root = root / "corpus" / "tasks" / task_id
            for directory in ("starter", "reference", "tests"):
                (task_root / directory).mkdir(parents=True, exist_ok=True)
            (task_root / "metadata.toml").write_text(
                "\n".join(
                    (
                        f'id = "{task_id}"',
                        'name = "Isolated task"',
                        'category = "packages"',
                        'difficulty = "easy"',
                        "timeout_seconds = 10",
                        "max_score = 100",
                        'systems = ["any"]',
                        'evaluator = "tests/check.sh"',
                        "[[criteria]]",
                        'id = "behavior"',
                        "points = 100",
                        "required = true",
                        'failure_class = "wrong-value"',
                        "",
                    )
                )
            )
            (task_root / "prompt.md").write_text("Write yes to answer.txt.\n")
            (task_root / "starter" / "answer.txt").write_text("no\n")
            fake_agent = task_root / "starter" / "fake-agent"
            fake_agent.write_text(
                "#!/bin/sh\n"
                f"test ! -e {task_root / 'tests' / 'check.sh'}\n"
                f"test ! -e {root / 'results'}\n"
                "while IFS= read -r line; do printf '%s\\n' \"$line\"; "
                "done < /proc/self/mountinfo > mountinfo.txt\n"
                "printf yes > answer.txt\n"
                "printf '%s\\n' '{\"type\":\"thread.started\"}' "
                "'{\"type\":\"turn.completed\"}'\n"
            )
            fake_agent.chmod(0o755)
            evaluator = task_root / "tests" / "check.sh"
            evaluator.write_text(
                "#!/bin/sh\n"
                "if test \"$(cat \"$1/answer.txt\")\" = yes; then ok=true; exit_code=0; "
                "else ok=false; exit_code=1; fi\n"
                "printf '{\"schema_version\":2,\"criteria\":{\"behavior\":%s}}\\n' "
                '"$ok" > "$NIXBENCH_SCORE_FILE"\n'
                "exit \"$exit_code\"\n"
            )
            evaluator.chmod(0o755)
            task = load_task(task_root)

            result = run_task(
                task,
                results_dir=root / "results",
                run_id="isolated-run",
                solution_mode="agent",
                agent_cmd="/workspace/fake-agent --json",
                completion_attestation="required",
                agent_adapter="codex-json-bwrap",
                isolation_profile="linux-bwrap-v1",
                network_policy="enabled",
                corpus_root=root / "corpus",
                keep_workdir=True,
            )

            self.assertTrue(result.passed, result.to_json())
            self.assertEqual(
                result.agent_status["preflight_evidence"],
                APPROVED_PREFLIGHT_EVIDENCE,
            )
            self.assertIsNotNone(result.workdir)
            self.addCleanup(
                shutil.rmtree, Path(result.workdir).parent, ignore_errors=True
            )
            mountinfo = (Path(result.workdir) / "mountinfo.txt").read_text()
            for forbidden_value in (
                task_id,
                str(root),
                str(task_root),
                str(task_root / "reference"),
                str(task_root / "tests" / "check.sh"),
                str(root / "results"),
                str(Path.home()),
            ):
                self.assertNotIn(forbidden_value, mountinfo)

    def test_runner_rejects_workspace_symlink_escape_before_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task_root = root / "corpus" / "tasks" / "isolated-task"
            for directory in ("starter", "reference", "tests"):
                (task_root / directory).mkdir(parents=True, exist_ok=True)
            (task_root / "metadata.toml").write_text(
                "\n".join(
                    (
                        'id = "isolated-task"',
                        'name = "Isolated task"',
                        'category = "packages"',
                        'difficulty = "easy"',
                        "timeout_seconds = 10",
                        "max_score = 100",
                        'systems = ["any"]',
                        'evaluator = "tests/check.sh"',
                        "[[criteria]]",
                        'id = "behavior"',
                        "points = 100",
                        "required = true",
                        'failure_class = "wrong-value"',
                        "",
                    )
                )
            )
            (task_root / "prompt.md").write_text("Do not escape.\n")
            (task_root / "reference" / "secret").write_text("reference-secret")
            fake_agent = task_root / "starter" / "fake-agent"
            ln_command = Path(shutil.which("ln") or "").resolve().with_name("ln")
            fake_agent.write_text(
                "#!/bin/sh\n"
                f"{ln_command} -s {task_root / 'reference' / 'secret'} leaked-reference\n"
                "printf '%s\\n' '{\"type\":\"thread.started\"}' "
                "'{\"type\":\"turn.completed\"}'\n"
            )
            fake_agent.chmod(0o755)
            marker = root / "evaluator-ran"
            evaluator = task_root / "tests" / "check.sh"
            evaluator.write_text(
                "#!/bin/sh\n"
                f"touch {marker}\n"
                'cat "$1/leaked-reference" >/dev/null\n'
                "printf '{\"schema_version\":2,\"criteria\":{\"behavior\":true}}\\n' "
                '> "$NIXBENCH_SCORE_FILE"\n'
                "exit 0\n"
            )
            evaluator.chmod(0o755)

            result = run_task(
                load_task(task_root),
                results_dir=root / "results",
                run_id="escape-run",
                solution_mode="agent",
                agent_cmd="/workspace/fake-agent --json",
                completion_attestation="required",
                agent_adapter="codex-json-bwrap",
                isolation_profile="linux-bwrap-v1",
                network_policy="enabled",
                corpus_root=root / "corpus",
            )

            self.assertEqual(result.measurement_status, "invalid")
            self.assertEqual(result.invalid_reason, "workspace-escape")
            self.assertFalse(marker.exists())

    def test_release_gates_are_specific_and_manifest_changes_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_corpus(root)
            evidence = [self.healthy_evidence()]

            provisional = check_release(
                root, health_evidence=evidence, verify_manifest=False
            )
            self.assertTrue(provisional["eligible"], provisional)
            self.assertIn("descriptive-only-category", provisional["warnings"])
            manifest = build_release_manifest(provisional, previous_version=None)
            manifest_path = root / "corpus" / "releases" / "1.0.0.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(manifest))

            checked = check_release(root, health_evidence=evidence)
            self.assertTrue(checked["eligible"], checked)

            broken_evidence = [{**evidence[0], "reject_fixture_count": 0}]
            broken = check_release(root, health_evidence=broken_evidence)
            failed = {gate["name"]: gate for gate in broken["gates"]}
            self.assertFalse(failed["independent-contract-fixtures"]["passed"])
            self.assertIn("rejecting fixture", failed["independent-contract-fixtures"]["reason"])

            evaluator = root / "tasks" / "task-a" / "tests" / "check.sh"
            evaluator.write_text(evaluator.read_text() + "\n# semantic change\n")
            changed = check_release(root, health_evidence=evidence)
            changed_gates = {gate["name"]: gate for gate in changed["gates"]}
            self.assertFalse(changed_gates["checked-release-manifest"]["passed"])
            self.assertIn("corpus digest", changed_gates["checked-release-manifest"]["reason"])

    def test_release_manifest_verifies_all_live_fields_and_task_change_claims(self) -> None:
        mutations = {
            "corpus_id": "wrong-corpus",
            "visibility": "retired",
            "task_count": 99,
            "category_counts": {"packages": 99},
            "difficulty_counts": {"hard": 1},
            "scoring_schema": "legacy-binary",
            "reporting": {},
            "active_tasks": [],
            "task_digests": {},
            "added_tasks": [],
            "changed_tasks": ["task-a"],
            "deprecated_tasks": ["task-a"],
        }
        for field, value in mutations.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.make_corpus(root)
                evidence = [self.healthy_evidence()]
                provisional = check_release(
                    root, health_evidence=evidence, verify_manifest=False
                )
                manifest = build_release_manifest(provisional, previous_version=None)
                manifest[field] = value
                manifest_path = root / "corpus" / "releases" / "1.0.0.json"
                manifest_path.parent.mkdir(parents=True)
                manifest_path.write_text(json.dumps(manifest))

                checked = check_release(root, health_evidence=evidence)
                gate = {item["name"]: item for item in checked["gates"]}[
                    "checked-release-manifest"
                ]

                self.assertFalse(gate["passed"], field)

    def test_quarantined_active_task_fails_release_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_corpus(root)
            (root / "corpus" / "task-lifecycle.toml").write_text(
                'schema_version = 1\nquarantined_tasks = ["task-a"]\n'
            )

            report = check_release(
                root,
                health_evidence=[self.healthy_evidence()],
                verify_manifest=False,
            )
            gates = {item["name"]: item for item in report["gates"]}

            self.assertFalse(gates["no-active-quarantined-tasks"]["passed"])

    def test_policy_file_gates_reject_category_deprecation_and_missing_note(self) -> None:
        mutations = (
            (
                "controlled-category-vocabulary",
                lambda root: (root / "corpus" / "category-vocabulary.toml").write_text(
                    'categories = ["modules"]\n'
                ),
            ),
            (
                "recorded-task-deprecations",
                lambda root: (root / "corpus" / "task-deprecations.toml").write_text(
                    'schema_version = 1\n[[deprecations]]\ntask_id = "task-a"\nreason = "fixture"\n'
                ),
            ),
            (
                "release-note",
                lambda root: (root / "docs" / "releases" / "1.0.0.md").write_text(""),
            ),
        )
        for gate_name, mutate in mutations:
            with self.subTest(gate=gate_name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                self.make_corpus(root)
                mutate(root)

                report = check_release(
                    root,
                    health_evidence=[self.healthy_evidence()],
                    verify_manifest=False,
                )
                gates = {gate["name"]: gate for gate in report["gates"]}

                self.assertFalse(gates[gate_name]["passed"])

    def test_private_small_corpus_bundle_suppresses_all_outcomes_and_sentinels(self) -> None:
        sentinel = "PRIVATE-TASK-SENTINEL-DO-NOT-LEAK"
        study = self.publication_study(
            task_ids=[sentinel], trial_count=1, corpus_visibility="private-heldout"
        )
        study.update({
            "study_id": "secret-study",
        })
        release_manifest = self.private_release_manifest(task_count=1)

        bundle = export_publication_bundle(
            study, release_manifest=release_manifest, redact_task_details=True
        )
        encoded = json.dumps(bundle, sort_keys=True)

        self.assertTrue(bundle["insufficient_aggregation"])
        self.assertNotIn(sentinel, encoded)
        for forbidden in (
            "score",
            "passed_tasks",
            "timeouts",
            "invalid_count",
            "task_count",
            "observations",
        ):
            self.assertNotIn(forbidden, bundle)

    def test_private_large_bundle_exports_only_aggregate_safe_strata(self) -> None:
        study = self.publication_study(
            task_ids=[f"private-task-{index}" for index in range(5)],
            trial_count=4,
            corpus_visibility="private-heldout",
        )

        bundle = export_publication_bundle(
            study,
            release_manifest=self.private_release_manifest(
                task_count=5, task_count_restricted=False
            ),
            redact_task_details=True,
        )
        encoded = json.dumps(bundle, sort_keys=True)

        self.assertFalse(bundle["insufficient_aggregation"])
        self.assertEqual(bundle["activeTaskCount"], 5)
        self.assertEqual(bundle["wholeCorpus"]["valid_observation_count"], 20)
        self.assertIn("packages", bundle["strata"]["categories"])
        self.assertNotIn("private-task-", encoded)
        self.assertNotIn("observations", encoded)
        for private_key in ("included_ids", "excluded_ids", "exclusion_reasons"):
            self.assertNotIn(private_key, encoded)

    def test_publication_export_calls_gate_and_uses_unique_valid_cells(self) -> None:
        study = self.publication_study(
            task_ids=["task-a", "task-b", "task-c", "task-d", "task-e"],
            trial_count=4,
            corpus_visibility="private-heldout",
        )
        manifest = self.private_release_manifest(task_count=5)
        study["attempts"] = []
        with self.assertRaisesRegex(ValueError, "publication is ineligible"):
            export_publication_bundle(
                study, release_manifest=manifest, redact_task_details=True
            )

        study = self.publication_study(
            task_ids=["task-a", "task-a", "task-a", "task-a", "SENTINEL-TASK"],
            trial_count=4,
            corpus_visibility="private-heldout",
        )
        with self.assertRaisesRegex(ValueError, "publication is ineligible"):
            export_publication_bundle(
                study, release_manifest=manifest, redact_task_details=True
            )

    def test_heldout_publication_requires_approved_isolation_evidence(self) -> None:
        study = self.publication_study(
            task_ids=["task-a"], trial_count=1, corpus_visibility="private-heldout"
        )
        manifest = self.private_release_manifest(task_count=1)

        study["metadata"]["isolation_profile"] = "local-workspace"
        rejected = check_publication(study, release_manifest=manifest)
        self.assertFalse(rejected["eligible"])
        self.assertIn("approved held-out isolation", " ".join(rejected["reasons"]))

        study["metadata"]["isolation_profile"] = "linux-bwrap-v1"
        accepted = check_publication(study, release_manifest=manifest)
        self.assertTrue(accepted["eligible"], accepted)

        study["metadata"]["corpus_visibility"] = "public"
        rejected = check_publication(study, release_manifest=manifest)
        self.assertIn("visibility", " ".join(rejected["reasons"]))

        study["metadata"]["corpus_visibility"] = "private-heldout"
        study["trials"][0]["agent_status"]["completed"] = False
        rejected = check_publication(study, release_manifest=manifest)
        self.assertIn("agent status", " ".join(rejected["reasons"]))

        study["trials"][0]["agent_status"]["completed"] = True
        study["metadata"]["agent_adapter_sha256"] = "f" * 64
        rejected = check_publication(study, release_manifest=manifest)
        self.assertIn("adapter digest", " ".join(rejected["reasons"]))

    def test_private_initializer_refuses_public_tree_and_creates_no_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            public_root = Path(temp) / "public"
            public_root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside the public repository"):
                initialize_private_corpus(
                    public_root / "private", public_repo_root=public_root
                )

            private_root = Path(temp) / "heldout"
            initialize_private_corpus(private_root, public_repo_root=public_root)

            self.assertIn(
                'visibility = "private-heldout"',
                (private_root / "corpus.toml").read_text(),
            )
            self.assertTrue(
                (private_root / "plans" / "001-first-heldout-release.md").is_file()
            )
            self.assertFalse((private_root / ".git").exists())
            self.assertFalse(any(private_root.rglob("metadata.toml")))

    def test_private_initializer_uses_actual_checkout_and_rejects_symlink_components(self) -> None:
        checkout = Path(__file__).resolve().parents[1]
        with self.assertRaisesRegex(ValueError, "outside the public repository"):
            initialize_private_corpus(
                checkout / ".private-corpus-must-not-exist",
                public_repo_root=Path(tempfile.gettempdir()),
            )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            actual = root / "actual"
            actual.mkdir()
            link = root / "link"
            link.symlink_to(actual, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                initialize_private_corpus(
                    link / "heldout", public_repo_root=checkout
                )

    def test_bubblewrap_probe_hides_forbidden_paths_and_allows_workspace_edits(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="nixbench-isolated-", dir="/tmp"
        ) as temp:
            root = Path(temp)
            workspace = root / "work"
            workspace.mkdir()
            forbidden = []
            for name in ("corpus", "reference", "evaluator", "results", "home"):
                path = root / name / "sentinel.txt"
                path.parent.mkdir()
                path.write_text(f"{name}-sentinel")
                forbidden.append(path)

            result = run_isolation_probe(
                workspace=workspace,
                forbidden_paths=forbidden,
                command=["/bin/sh", "-c", "printf edited > probe.txt"],
                network_policy="enabled",
            )

            self.assertTrue(result["successful"], result)
            self.assertTrue(result["forbidden_paths_absent"])
            self.assertTrue(result["neutral_mounts"])
            self.assertTrue(result["generic_forbidden_surfaces_absent"])
            self.assertTrue(result["nix_daemon_absent"])
            self.assertEqual((workspace / "probe.txt").read_text(), "edited")

    def test_disabled_network_policy_requests_a_separate_network_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp)

            disabled = build_bubblewrap_command(
                workspace=workspace,
                forbidden_paths=[],
                command=["/bin/sh", "-c", ":"],
                network_policy="disabled",
            )
            enabled = build_bubblewrap_command(
                workspace=workspace,
                forbidden_paths=[],
                command=["/bin/sh", "-c", ":"],
                network_policy="enabled",
            )

            self.assertIn("--unshare-net", disabled)
            self.assertNotIn("--unshare-net", enabled)

    def test_isolation_probe_rejects_a_non_neutral_workspace_mount(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = Path(temp) / "task-id-leaking-workspace"
            workspace.mkdir()

            result = run_isolation_probe(
                workspace=workspace,
                forbidden_paths=[],
                command=["/bin/sh", "-c", "printf should-not-run > marker"],
                network_policy="enabled",
            )

            self.assertFalse(result["successful"])
            self.assertEqual(result["returncode"], 125)
            self.assertFalse(result["neutral_mounts"])
            self.assertFalse((workspace / "marker").exists())

    def test_isolation_probe_requires_its_structured_preflight_record(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="nixbench-isolated-", dir="/tmp"
        ) as temp:
            workspace = Path(temp) / "work"
            workspace.mkdir()

            result = run_isolation_probe(
                workspace=workspace,
                forbidden_paths=[],
                command=[
                    "/bin/sh",
                    "-c",
                    ": > .nixbench-isolation-preflight",
                ],
                network_policy="enabled",
            )

            self.assertEqual(result["returncode"], 0)
            self.assertFalse(result["successful"])
            self.assertIsNone(result["evidence"])

    def test_isolation_probe_evidence_is_independent_of_test_command_exit(self) -> None:
        with tempfile.TemporaryDirectory(
            prefix="nixbench-isolated-", dir="/tmp"
        ) as temp:
            workspace = Path(temp) / "work"
            workspace.mkdir()

            result = run_isolation_probe(
                workspace=workspace,
                forbidden_paths=[],
                command=["/bin/sh", "-c", "exit 7"],
                network_policy="enabled",
            )

            self.assertFalse(result["successful"])
            self.assertEqual(result["returncode"], 7)
            self.assertTrue(result["generic_forbidden_surfaces_absent"])
            self.assertTrue(result["neutral_mounts"])
            self.assertTrue(result["workspace_writable"])
            self.assertTrue(result["nix_daemon_absent"])

    def test_ci_and_nix_shell_provide_bubblewrap(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertIn("bubblewrap", (root / ".github/workflows/tests.yml").read_text())
        self.assertIn("pkgs.bubblewrap", (root / "flake.nix").read_text())

    @staticmethod
    def private_release_manifest(
        *, task_count: int, task_count_restricted: bool = True
    ) -> dict[str, object]:
        adapter_digest = get_trusted_adapter("codex-json-bwrap").sha256
        return {
            "corpus_id": "private-corpus",
            "corpus_version": "1.0.0",
            "corpus_digest": "d" * 64,
            "visibility": "private-heldout",
            "task_count": task_count,
            "required_protocol_schema_version": 2,
            "reporting": {"report_schema_version": 1},
            "task_count_restricted": task_count_restricted,
            "trusted_isolation": {
                "profile": "linux-bwrap-v1",
                "adapter": "codex-json-bwrap",
                "adapter_sha256": adapter_digest,
                "attestation_trust": "approved-linux-bwrap-v1",
                "preflight_evidence": APPROVED_PREFLIGHT_EVIDENCE,
            },
        }

    @classmethod
    def publication_study(
        cls,
        *,
        task_ids: list[str],
        trial_count: int,
        corpus_visibility: str,
    ) -> dict[str, object]:
        adapter_digest = get_trusted_adapter("codex-json-bwrap").sha256
        trials = []
        for run in range(trial_count):
            observations = []
            for index, task_id in enumerate(task_ids):
                observations.append(
                    {
                        "task_id": task_id,
                        "category": "packages",
                        "difficulty": "medium",
                        "measurement_status": "valid",
                        "passed": index % 2 == 0,
                        "score": 100 if index % 2 == 0 else 50,
                        "max_score": 100,
                        "normalized_score": 1.0 if index % 2 == 0 else 0.5,
                        "passed_criteria": ["behavior"] if index % 2 == 0 else [],
                        "failed_criteria": [] if index % 2 == 0 else ["behavior"],
                        "failure_classes": [] if index % 2 == 0 else ["wrong-value"],
                        "agent_duration_seconds": 1,
                        "evaluator_duration_seconds": 0.1,
                        "agent_timeout": False,
                        "infrastructure_events": [],
                    }
                )
            trials.append(
                {
                    "run_id": f"run-{run}",
                    "measurement_status": "valid",
                    "task_count": len(task_ids),
                    "scoring_schema": "criteria-v2",
                    "observations": observations,
                    "agent_status": {
                        "task_count": len(task_ids),
                        "preflight_successful": True,
                        "completed": True,
                        "preflight_evidence": APPROVED_PREFLIGHT_EVIDENCE,
                    },
                }
            )
        return {
            "study_id": "private-study",
            "metadata": {
                "corpus_id": "private-corpus",
                "corpus_version": "1.0.0",
                "corpus_digest": "d" * 64,
                "corpus_visibility": corpus_visibility,
                "configuration_id": "cfg-private",
                "protocol_id": "protocol-private",
                "protocol_schema_version": 2,
                "protocol_complete": True,
                "model_identity_evidence": "vendor-api-direct",
                "timing_environment_id": "timing-a",
                "completion_attestation": "required",
                "wrapper_prompt_sha256": "a" * 64,
                "agent_command_sha256": "b" * 64,
                "agent_adapter": "codex-json-bwrap",
                "agent_adapter_sha256": adapter_digest,
                "attestation_trust": "approved-linux-bwrap-v1",
                "isolation_profile": "linux-bwrap-v1",
            },
            "task_count": len(task_ids),
            "trials": trials,
            "attempts": [
                {
                    "run_id": trial["run_id"],
                    "measurement_status": "valid",
                    "included_in_trials": True,
                }
                for trial in trials
            ],
        }

    @staticmethod
    def healthy_evidence() -> dict[str, object]:
        return {
            "task_id": "task-a",
            "category": "packages",
            "difficulty": "easy",
            "reference_full_score": True,
            "starter_rejected": True,
            "pass_fixture_count": 1,
            "reject_fixture_count": 1,
            "criterion_ids": ["behavior"],
            "criterion_coverage": ["behavior"],
            "evaluator_deterministic": True,
            "contract_outcomes_match": True,
            "invalid_measurement_count": 0,
            "evaluator_durations_seconds": [0.01, 0.02],
            "timeout_seconds": 10,
            "known_issue_count": 0,
        }

    @staticmethod
    def make_corpus(root: Path) -> None:
        (root / "corpus.toml").write_text(
            "\n".join(
                (
                    "schema_version = 1",
                    'id = "fixture-corpus"',
                    'version = "1.0.0"',
                    'visibility = "public"',
                    "",
                )
            )
        )
        task = root / "tasks" / "task-a"
        for directory in ("starter", "reference", "tests"):
            (task / directory).mkdir(parents=True, exist_ok=True)
        (task / "metadata.toml").write_text(
            "\n".join(
                (
                    'id = "task-a"',
                    'name = "Task A"',
                    'category = "packages"',
                    'difficulty = "easy"',
                    "timeout_seconds = 10",
                    "max_score = 100",
                    'systems = ["any"]',
                    'evaluator = "tests/check.sh"',
                    "[[criteria]]",
                    'id = "behavior"',
                    "points = 100",
                    "required = true",
                    'failure_class = "wrong-value"',
                    "",
                )
            )
        )
        (task / "prompt.md").write_text("Do the fixture task.\n")
        (task / "starter" / "answer.txt").write_text("no\n")
        (task / "reference" / "answer.txt").write_text("yes\n")
        evaluator = task / "tests" / "check.sh"
        evaluator.write_text("#!/bin/sh\nexit 1\n")
        evaluator.chmod(0o755)
        case = root / "contracts" / "task-a" / "pass"
        (case / "candidate").mkdir(parents=True)
        (case / "candidate" / "answer.txt").write_text("yes\n")
        (case / "case.toml").write_text(
            'task_id = "task-a"\noutcome = "pass"\ncriterion_id = "behavior"\n'
        )
        reject = root / "contracts" / "task-a" / "reject"
        (reject / "candidate").mkdir(parents=True)
        (reject / "candidate" / "answer.txt").write_text("no\n")
        (reject / "case.toml").write_text(
            'task_id = "task-a"\noutcome = "reject"\ncriterion_id = "behavior"\n'
        )
        (root / "corpus").mkdir()
        (root / "corpus" / "category-vocabulary.toml").write_text(
            'categories = ["packages"]\n'
        )
        (root / "corpus" / "task-deprecations.toml").write_text(
            "schema_version = 1\ndeprecations = []\n"
        )
        (root / "corpus" / "task-lifecycle.toml").write_text(
            "schema_version = 1\nquarantined_tasks = []\n"
        )
        notes = root / "docs" / "releases"
        notes.mkdir(parents=True)
        (notes / "1.0.0.md").write_text("# Fixture 1.0.0\n\nInitial release.\n")


if __name__ == "__main__":
    unittest.main()
