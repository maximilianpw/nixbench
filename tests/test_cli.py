from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nixbench.cli import build_parser, main
from tests.test_runner import make_toy_task


class CliTests(unittest.TestCase):
    def test_report_study_emits_versioned_canonical_json(self) -> None:
        fixture = (
            Path(__file__).parent
            / "fixtures"
            / "studies"
            / "complete-v2"
            / "summary.json"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root, "report-study", "--study-path", str(fixture), "--json"
            )

        report = json.loads(stdout)
        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(report["schema_version"], 1)
        self.assertFalse(report["aggregate_only"])
        self.assertIn("whole_corpus", report["strata"])

    def test_corpus_health_writes_digest_keyed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)
            studies = results_dir / "studies"
            studies.mkdir()
            output = results_dir / "health.json"
            evidence = [
                {
                    "task_id": "toy",
                    "category": "packages",
                    "difficulty": "easy",
                    "reference_full_score": True,
                    "starter_rejected": True,
                    "pass_fixture_count": 1,
                    "reject_fixture_count": 1,
                    "criterion_ids": [],
                    "criterion_coverage": [],
                    "evaluator_deterministic": True,
                    "evaluator_durations_seconds": [0.01, 0.01],
                }
            ]

            with patch("nixbench.cli._collect_corpus_health_evidence", return_value=evidence):
                returncode, stdout, stderr = invoke_cli(
                    root,
                    results_dir,
                    "corpus-health",
                    "--studies-dir",
                    str(studies),
                    "--contracts-dir",
                    str(root / "contracts"),
                    "--output",
                    str(output),
                )

            payload = json.loads(output.read_text())

        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")
        self.assertIn("wrote corpus health", stdout)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(len(payload["corpora"]), 1)

    def test_corpus_health_collects_evaluator_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)
            studies = results_dir / "studies"
            studies.mkdir()
            output = results_dir / "health.json"

            returncode, _, stderr = invoke_cli(
                root,
                results_dir,
                "corpus-health",
                "--studies-dir",
                str(studies),
                "--contracts-dir",
                str(root / "contracts"),
                "--output",
                str(output),
            )
            payload = json.loads(output.read_text())
            health = next(iter(payload["corpora"].values()))

        self.assertEqual(returncode, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(health["tasks"]["toy"]["reference_full_score"])
        self.assertTrue(health["tasks"]["toy"]["starter_rejected"])
        self.assertTrue(health["tasks"]["toy"]["evaluator_deterministic"])

    def test_run_all_checkpoints_harness_exception_before_stopping(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            with patch("nixbench.cli.run_task", side_effect=RuntimeError("boom")):
                returncode, stdout, stderr = invoke_cli(
                    root, results_dir, "run-all", "--solution", "reference"
                )

            self.assertEqual(returncode, 2)
            self.assertIn("checkpointed before stopping", stderr)
            study = json.loads(next((results_dir / "studies").glob("*/summary.json")).read_text())
            self.assertEqual(study["trial_count"], 0)
            self.assertEqual(study["attempts"][0]["measurement_status"], "incomplete")
            self.assertIn("harness-exception", study["attempts"][0]["exclusion_reasons"])

    def test_run_all_checkpoints_interruption_before_reraising(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            with patch("nixbench.cli.run_task", side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
                invoke_cli(root, results_dir, "run-all", "--solution", "reference")

            study = json.loads(next((results_dir / "studies").glob("*/summary.json")).read_text())
            self.assertEqual(study["trial_count"], 0)
            self.assertIn("interrupted", study["attempts"][0]["exclusion_reasons"])

    def test_run_all_accepts_pi_agent_kind(self) -> None:
        args = build_parser().parse_args(["run-all", "--kind", "pi"])
        self.assertEqual(args.kind, "pi")

    def test_corpus_id_reports_external_corpus_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(root, "corpus-id", "--json")
            identity = json.loads(stdout)

            self.assertEqual(returncode, 0)
            self.assertEqual(stderr, "")
            self.assertEqual(identity["id"], "toy-corpus")
            self.assertEqual(identity["task_count"], 1)
            self.assertEqual(len(identity["digest"]), 64)

    def test_validate_accepts_failing_starter_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_passing_starter_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root, check_script="exit 0\n")

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_accepts_passing_reference_solution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "reference",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 reference outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_an_under_scored_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":5}\' > "$NIXBENCH_SCORE_FILE"\nexit 0\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "reference",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 reference outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_full_scored_starter_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":10}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_accepts_a_partial_scored_starter_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":5}\' > "$NIXBENCH_SCORE_FILE"\nexit 1\n',
            )

            returncode, stdout, stderr = run_cli(
                root,
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("1/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_timed_out_starter_evaluator(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root, check_script="sleep 2\n")
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(metadata_path.read_text().replace("timeout_seconds = 5", "timeout_seconds = 1"))

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_an_invalid_starter_score(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(
                root,
                check_script='printf \'{"score":NaN}\' > "$NIXBENCH_SCORE_FILE"\nexit 0\n',
            )

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_validate_rejects_a_starter_evaluator_infrastructure_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root, check_script="exit 2\n")

            returncode, stdout, stderr = run_cli(root, "validate", "--solution", "starter")

            self.assertEqual(returncode, 1)
            self.assertIn("0/1 starter outcomes matched expectations", stdout)
            self.assertEqual(stderr, "")

    def test_run_all_rejects_an_empty_task_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            returncode, stdout, stderr = run_cli(root, "run-all", "--solution", "starter")

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("error: no tasks", stderr)

    def test_execution_rejects_a_results_directory_inside_the_task_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                root / "results",
                "validate",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("--results-dir must be outside --tasks-dir", stderr)

    def test_run_all_rejects_an_empty_system_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(
                metadata_path.read_text().replace('systems = ["any"]', 'systems = ["x86_64-linux"]')
            )

            returncode, stdout, stderr = run_cli(
                root,
                "--system",
                "aarch64-darwin",
                "run-all",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("support system aarch64-darwin", stderr)

    def test_run_rejects_an_unsupported_task_without_reporting_a_skip(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            task = make_toy_task(root)
            metadata_path = task.root / "metadata.toml"
            metadata_path.write_text(
                metadata_path.read_text().replace('systems = ["any"]', 'systems = ["x86_64-linux"]')
            )

            returncode, stdout, stderr = run_cli(
                root,
                "--system",
                "aarch64-darwin",
                "run",
                "toy",
                "--solution",
                "starter",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("no task was run", stderr)

    def test_run_all_repeats_trials_and_writes_a_study_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "2",
                "--model",
                "toy-model",
                "--effort",
                "high",
                "--kind",
                "opencode",
            )

            self.assertEqual(returncode, 0)
            self.assertIn("trial 1/2", stdout)
            self.assertIn("trial 2/2", stdout)
            self.assertEqual(stderr, "")
            study_paths = list((results_dir / "studies").glob("*/summary.json"))
            self.assertEqual(len(study_paths), 1)
            study = json.loads(study_paths[0].read_text())
            self.assertEqual(study["trial_count"], 2)
            self.assertEqual(study["metadata"]["model"], "toy-model")
            self.assertEqual(study["metadata"]["effort"], "high")
            self.assertEqual(study["metadata"]["kind"], "opencode")
            self.assertFalse(study["metadata"]["protocol_complete"])
            self.assertEqual(study["metadata"]["corpus_id"], "toy-corpus")
            self.assertEqual(
                study["trials"][0]["configuration_id"],
                study["metadata"]["configuration_id"],
            )
            self.assertEqual(study["schema_version"], 3)
            self.assertEqual(
                study["trials"][0]["observations"][0]["task_digest"],
                study["metadata"]["corpus_task_digests"]["toy"],
            )

    def test_run_all_records_complete_protocol_without_raw_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)
            wrapper = root / "wrapper.txt"
            wrapper.write_text("Edit the task.\n")
            protocol = root / "protocol.toml"
            write_protocol(protocol, system="toy-system")
            fake_codex = root / "fake-codex.py"
            fake_codex.write_text(
                """#!/usr/bin/env python3
import json
from pathlib import Path
Path("answer.txt").write_text("reference\\n")
print(json.dumps({"type": "thread.started", "thread_id": "test"}))
print(json.dumps({"type": "turn.completed"}))
"""
            )
            fake_codex.chmod(0o755)
            agent_command = f"{fake_codex} exec --json"

            returncode, _, stderr = invoke_cli(
                root,
                results_dir,
                "--system",
                "toy-system",
                "run-all",
                "--agent-cmd",
                agent_command,
                "--agent-adapter",
                "codex-json",
                "--protocol-file",
                str(protocol),
                "--wrapper-prompt-file",
                str(wrapper),
            )

            self.assertEqual(returncode, 0)
            self.assertEqual(stderr, "")
            study_path = next((results_dir / "studies").glob("*/summary.json"))
            study = json.loads(study_path.read_text())
            metadata = study["metadata"]
            self.assertTrue(metadata["protocol_complete"])
            self.assertEqual(metadata["protocol_id"], "test-profile")
            self.assertEqual(metadata["model"], "toy-model")
            self.assertEqual(metadata["effort"], "test")
            self.assertEqual(metadata["network"], "disabled")
            self.assertEqual(len(metadata["agent_command_sha256"]), 64)
            self.assertEqual(metadata["agent_adapter"], "codex-json")
            self.assertEqual(len(metadata["agent_adapter_sha256"]), 64)
            self.assertEqual(metadata["attestation_trust"], "provisional-same-uid")
            self.assertNotIn(agent_command, study_path.read_text())

            count_code, count_stdout, count_stderr = invoke_cli(
                root,
                results_dir,
                "--system",
                "toy-system",
                "study-count",
                "--protocol-file",
                str(protocol),
                "--wrapper-prompt-file",
                str(wrapper),
                "--agent-cmd",
                agent_command,
                "--agent-adapter",
                "codex-json",
            )
            self.assertEqual(count_code, 0)
            self.assertEqual(count_stdout, "1\n")
            self.assertEqual(count_stderr, "")

    def test_run_all_rejects_cli_metadata_that_conflicts_with_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            make_toy_task(root)
            wrapper = root / "wrapper.txt"
            wrapper.write_text("Edit the task.\n")
            protocol = root / "protocol.toml"
            write_protocol(protocol, system="toy-system")

            returncode, stdout, stderr = invoke_cli(
                root,
                Path(results),
                "--system",
                "toy-system",
                "run-all",
                "--agent-cmd",
                "printf 'reference\\n' > answer.txt",
                "--protocol-file",
                str(protocol),
                "--wrapper-prompt-file",
                str(wrapper),
                "--model",
                "different-model",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("--model does not match protocol model_id", stderr)

    def test_run_all_rejects_zero_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_toy_task(root)

            returncode, stdout, stderr = run_cli(
                root,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "0",
            )

            self.assertEqual(returncode, 2)
            self.assertEqual(stdout, "")
            self.assertIn("--trials must be at least 1", stderr)

    def test_repeated_study_stops_on_agent_infrastructure_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--agent-cmd",
                "exit 7",
                "--trials",
                "2",
            )

            self.assertEqual(returncode, 2)
            self.assertIn("trial 1/2", stdout)
            self.assertIn("agent-process-error", stderr)
            study_path = next((results_dir / "studies").glob("*/summary.json"))
            study = json.loads(study_path.read_text())
            self.assertEqual(study["trial_count"], 0)
            self.assertEqual(study["attempt_count"], 1)
            self.assertEqual(study["attempts"][0]["measurement_status"], "invalid")

    def test_repeated_study_checkpoints_evaluator_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root, check_script="exit 2\n")

            returncode, _, stderr = invoke_cli(
                root, results_dir, "run-all", "--solution", "starter", "--trials", "2"
            )

            self.assertEqual(returncode, 2)
            self.assertIn("evaluator-error", stderr)
            study = json.loads(next((results_dir / "studies").glob("*/summary.json")).read_text())
            self.assertEqual(study["trial_count"], 0)
            self.assertEqual(study["attempts"][0]["exclusion_reasons"], ["evaluator-error"])

    def test_repeated_study_checkpoints_evaluator_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            task = make_toy_task(root, check_script="sleep 2\n")
            metadata = task.root / "metadata.toml"
            metadata.write_text(metadata.read_text().replace("timeout_seconds = 5", "timeout_seconds = 1"))

            returncode, _, stderr = invoke_cli(
                root, results_dir, "run-all", "--solution", "starter", "--trials", "2"
            )

            self.assertEqual(returncode, 2)
            self.assertIn("evaluator-timeout", stderr)
            study = json.loads(next((results_dir / "studies").glob("*/summary.json")).read_text())
            self.assertEqual(study["trial_count"], 0)
            self.assertEqual(study["attempts"][0]["exclusion_reasons"], ["evaluator-timeout"])

    def test_study_count_prints_completed_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            make_toy_task(root)
            returncode, _, _ = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--solution",
                "reference",
                "--trials",
                "2",
                "--series",
                "toy",
                "--effort",
                "high",
            )
            self.assertEqual(returncode, 0)

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "study-count",
                "--series",
                "toy",
                "--effort",
                "high",
                "--task-count",
                "1",
            )

            self.assertEqual(returncode, 0)
            self.assertEqual(stdout, "2\n")
            self.assertIn("study counting is deprecated", stderr)

    def test_repeated_study_checkpoints_valid_trials_before_a_later_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as results:
            root = Path(temp)
            results_dir = Path(results)
            counter = root / "agent-count"
            make_toy_task(root)
            agent_cmd = (
                f'count=$(cat "{counter}" 2>/dev/null || printf 0); '
                'count=$((count + 1)); '
                f'printf "%s" "$count" > "{counter}"; '
                'if [ "$count" -eq 1 ]; then printf "reference\\n" > answer.txt; exit 0; fi; '
                'exit 7'
            )

            returncode, stdout, stderr = invoke_cli(
                root,
                results_dir,
                "run-all",
                "--agent-cmd",
                agent_cmd,
                "--trials",
                "2",
                "--series",
                "toy",
                "--effort",
                "high",
            )

            self.assertEqual(returncode, 2)
            self.assertIn("study checkpoint: 1/2", stdout)
            self.assertIn("agent-process-error", stderr)
            study_paths = list((results_dir / "studies").glob("*/summary.json"))
            self.assertEqual(len(study_paths), 1)
            study = json.loads(study_paths[0].read_text())
            self.assertEqual(study["trial_count"], 1)
            self.assertEqual(study["attempt_count"], 2)
            self.assertEqual(study["attempts"][1]["measurement_status"], "invalid")


def attested_agent_command(command: str) -> str:
    status = json.dumps(
        {
            "schema_version": 1,
            "preflight": {
                "successful": True,
                "evidence": "synthetic-native-completion-event",
            },
            "completed": True,
            "transport_error": None,
            "launcher_exit": 0,
        },
        separators=(",", ":"),
    )
    return (
        command
        + "; printf '%s' "
        + repr(status)
        + ' > "$NIXBENCH_AGENT_STATUS_FILE.tmp"'
        + '; mv "$NIXBENCH_AGENT_STATUS_FILE.tmp" "$NIXBENCH_AGENT_STATUS_FILE"'
    )


def write_protocol(path: Path, *, system: str) -> None:
    path.write_text(
        "\n".join(
            [
                "schema_version = 2",
                'id = "test-profile"',
                'harness_id = "nixbench"',
                'harness_version = "1.0"',
                'model_id = "toy-model"',
                'model_identity_evidence = "unverified"',
                'effort = "test"',
                'network_policy = "disabled"',
                'isolation_profile = "test"',
                'tool_policy = "test"',
                'completion_attestation = "required"',
                'agent_adapter = "codex-json"',
                "agent_timeout_seconds = 300",
                f'system = "{system}"',
                "",
            ]
        )
    )


def run_cli(tasks_dir: Path, *args: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as results:
        return invoke_cli(tasks_dir, Path(results), *args)


def invoke_cli(tasks_dir: Path, results_dir: Path, *args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    argv = [
        "--tasks-dir",
        str(tasks_dir),
        "--results-dir",
        str(results_dir),
        *args,
    ]
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        returncode = main(argv)
    return returncode, stdout.getvalue(), stderr.getvalue()


if __name__ == "__main__":
    unittest.main()
