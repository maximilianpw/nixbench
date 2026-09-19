from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nixbench.export import export_studies_for_site


class ExportTests(unittest.TestCase):
    def test_filters_malformed_unpublished_and_non_site_before_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unpublished = root / "studies" / "unpublished" / "summary.json"
            unpublished.parent.mkdir(parents=True)
            unpublished.write_text(
                json.dumps(
                    {
                        "metadata": {**self.site_metadata(), "publish": False},
                        "trials": "malformed",
                    }
                )
            )
            generic = root / "studies" / "generic" / "summary.json"
            generic.parent.mkdir(parents=True)
            generic.write_text(
                json.dumps(
                    {
                        "metadata": {"solution": "reference"},
                        "trials": "malformed",
                    }
                )
            )
            valid = root / "studies" / "valid" / "summary.json"
            valid.parent.mkdir(parents=True)
            valid.write_text(
                json.dumps(
                    {
                        "study_id": "valid",
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [self.trial("valid-run")],
                    }
                )
            )

            count = export_studies_for_site(
                root, root / "out.json", allow_legacy_protocol=True
            )

        self.assertEqual(count, 1)

    def test_aggregate_sibling_does_not_erase_configuration_observations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = {
                **self.site_metadata(),
                "protocol_complete": False,
                "configuration_id": "cfg-a",
                "corpus_digest": "c" * 64,
            }
            observation = {
                "task_id": "task-a",
                "task_digest": "task-a-digest",
                "category": "packages",
                "difficulty": "medium",
                "measurement_status": "valid",
                "task_outcome": "fail",
                "passed": False,
                "score": 75,
                "max_score": 100,
                "normalized_score": 0.75,
                "passed_criteria": [],
                "failed_criteria": ["behavior"],
                "failure_classes": ["wrong-value"],
                "agent_duration_seconds": 1,
                "evaluator_duration_seconds": 0.1,
                "agent_timeout": False,
                "infrastructure_events": [],
            }
            observed_trial = {
                "run_id": "observed-run",
                "measurement_status": "valid",
                "passed_tasks": 0,
                "failed_tasks": 1,
                "task_count": 1,
                "score": 75,
                "max_score": 100,
                "score_rate": 0.75,
                "agent_time_seconds": 1,
                "agent_seconds_per_task": 1,
                "timeouts": 0,
                "scoring_schema": "criteria-v2",
                "configuration_id": "cfg-a",
                "corpus_digest": "c" * 64,
                "observations": [observation],
            }
            aggregate_trial = {
                **self.trial("aggregate-run"),
                "passed_tasks": 1,
                "failed_tasks": 0,
                "score": 100,
                "max_score": 100,
                "task_count": 1,
                "configuration_id": "cfg-a",
                "corpus_digest": "c" * 64,
            }
            for study_id, task_count, trial_value in (
                ("observed", 1, observed_trial),
                ("aggregate", 1, aggregate_trial),
            ):
                path = root / "studies" / study_id / "summary.json"
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps(
                        {
                            "study_id": study_id,
                            "task_count": task_count,
                            "metadata": metadata,
                            "trials": [trial_value],
                        }
                    )
                )

            count = export_studies_for_site(
                root, root / "out.json", allow_legacy_protocol=True
            )
            rows = json.loads((root / "out.json").read_text())

        self.assertEqual(count, 2)
        observed_row = next(row for row in rows if row["runId"] == "observed-run")
        self.assertFalse(observed_row["canonicalReport"]["aggregate_only"])
        self.assertEqual(
            observed_row["canonicalReport"]["strata"]["whole_corpus"]["macro_task_score"],
            0.75,
        )
        self.assertEqual(
            observed_row["canonicalReport"]["excluded_trials"][0]["run_id"],
            "aggregate-run",
        )

    def test_exports_observations_and_canonical_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "current" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0",
                "corpus_visibility": "public",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_schema_version": 2,
                "protocol_complete": True,
                "completion_attestation": "required",
                "model_identity_evidence": "vendor-api-direct",
                "configuration_id": "cfg-stored",
                "timing_environment_id": "timing-stored",
                "wrapper_prompt_sha256": "b" * 64,
                "agent_command_sha256": "a" * 64,
                "agent_adapter": "codex-json",
                "agent_adapter_sha256": "d" * 64,
                "attestation_trust": "provisional-same-uid",
            }
            observation = {
                "task_id": "task-a",
                "task_digest": "task-digest",
                "category": "packages",
                "difficulty": "medium",
                "measurement_status": "valid",
                "task_outcome": "fail",
                "passed": False,
                "score": 75,
                "max_score": 100,
                "normalized_score": 0.75,
                "passed_criteria": ["evaluation"],
                "failed_criteria": ["behavior"],
                "failure_classes": ["wrong-value"],
                "agent_duration_seconds": 4,
                "evaluator_duration_seconds": 0.2,
                "agent_timeout": False,
                "infrastructure_events": [],
            }
            trial = {
                "run_id": "current-run",
                "measurement_status": "valid",
                "passed_tasks": 0,
                "failed_tasks": 1,
                "task_count": 1,
                "score": 75,
                "max_score": 100,
                "score_rate": 0.75,
                "agent_time_seconds": 4,
                "agent_seconds_per_task": 4,
                "timeouts": 0,
                "scoring_schema": "criteria-v2",
                "corpus_digest": "c" * 64,
                "configuration_id": "cfg-stored",
                "observations": [observation],
            }
            summary_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "study_id": "current",
                        "task_count": 1,
                        "trial_count": 1,
                        "metadata": metadata,
                        "trials": [trial],
                        "attempt_count": 2,
                        "attempts": [
                            {"run_id": "current-run", "measurement_status": "valid"},
                            {
                                "run_id": "bad-run",
                                "measurement_status": "invalid",
                                "exclusion_reasons": ["evaluator-error"],
                            },
                        ],
                    }
                )
            )
            unpublished = root / "studies" / "unpublished" / "summary.json"
            unpublished.parent.mkdir(parents=True)
            unpublished_trial = {
                **trial,
                "run_id": "unpublished-run",
                "score": 0,
                "score_rate": 0,
                "observations": [
                    {
                        **observation,
                        "score": 0,
                        "normalized_score": 0,
                    }
                ],
            }
            unpublished.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "study_id": "unpublished",
                        "task_count": 1,
                        "trial_count": 1,
                        "metadata": {**metadata, "publish": False},
                        "trials": [unpublished_trial],
                    }
                )
            )

            export_studies_for_site(root, root / "out.json")
            row = json.loads((root / "out.json").read_text())[0]

            self.assertEqual(row["observations"], [observation])
            self.assertEqual(row["invalidMeasurementCount"], 1)
            self.assertFalse(row["aggregateOnly"])
            self.assertEqual(row["canonicalReport"]["schema_version"], 1)
            self.assertEqual(
                row["canonicalReport"]["strata"]["whole_corpus"]["macro_task_score"],
                0.75,
            )
            self.assertEqual(row["stratumCounts"]["wholeCorpusTaskCount"], 1)

    def test_provisional_attestation_rejects_held_out_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "studies" / "held-out" / "summary.json"
            path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "held-out",
                "corpus_version": "1.0.0",
                "corpus_visibility": "private",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_schema_version": 1,
                "protocol_complete": True,
                "completion_attestation": "required",
                "agent_adapter": "codex-json",
                "agent_adapter_sha256": "d" * 64,
                "attestation_trust": "provisional-same-uid",
                "configuration_id": "cfg-held-out",
                "timing_environment_id": "timing-held-out",
                "wrapper_prompt_sha256": "b" * 64,
                "agent_command_sha256": "a" * 64,
            }
            trial = {
                **self.trial("held-out-run"),
                "corpus_digest": "c" * 64,
                "configuration_id": "cfg-held-out",
            }
            path.write_text(json.dumps({"task_count": 29, "metadata": metadata, "trials": [trial]}))

            with self.assertRaisesRegex(ValueError, "approved isolation evidence"):
                export_studies_for_site(root, root / "out.json")

    def test_site_export_refuses_private_and_retired_studies_before_hydration(self) -> None:
        for visibility in ("private-heldout", "retired"):
            with self.subTest(visibility=visibility), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = root / "studies" / visibility / "summary.json"
                path.parent.mkdir(parents=True)
                path.write_text(
                    json.dumps(
                        {
                            "metadata": {
                                **self.site_metadata(),
                                "publish": True,
                                "corpus_visibility": visibility,
                            },
                            "trials": "malformed-private-sentinel",
                        }
                    )
                )

                with self.assertRaisesRegex(ValueError, "cannot be exported to the public site"):
                    export_studies_for_site(root, root / "out.json")

                self.assertFalse((root / "out.json").exists())

    def test_zero_trial_attempt_ledger_is_skipped_beside_valid_study(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty = root / "studies" / "empty" / "summary.json"
            empty.parent.mkdir(parents=True)
            empty.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "study_id": "empty",
                        "task_count": 29,
                        "trial_count": 0,
                        "metadata": {"protocol_complete": False},
                        "trials": [],
                        "attempts": [
                            {
                                "measurement_status": "invalid",
                                "exclusion_reasons": ["evaluator-timeout"],
                            },
                            {
                                "measurement_status": "invalid",
                                "exclusion_reasons": ["evaluator-error"],
                            },
                        ],
                    }
                )
            )
            valid = root / "studies" / "valid" / "summary.json"
            valid.parent.mkdir(parents=True)
            valid.write_text(
                json.dumps(
                    {
                        "study_id": "valid",
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [self.trial("valid-run")],
                    }
                )
            )

            count = export_studies_for_site(
                root, root / "out.json", allow_legacy_protocol=True
            )

            self.assertEqual(count, 1)
            self.assertEqual(json.loads((root / "out.json").read_text())[0]["runId"], "valid-run")
            self.assertEqual(len(json.loads(empty.read_text())["attempts"]), 2)

    def test_exports_site_rows_from_study_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "results" / "studies" / "study-1" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {
                            "label": "GPT Test via Codex CLI",
                            "model": "gpt-test",
                            "series": "gptTest",
                            "effort": "high",
                            "marker": "TH",
                            "kind": "codex",
                            "agent_version": "codex-cli test",
                            "corpus_revision": "abc123",
                            "host": "test-host",
                            "network": "offline",
                        },
                        "trials": [
                            {
                                "run_id": "run-1",
                                "passed_tasks": 22,
                                "failed_tasks": 7,
                                "score": 2200,
                                "max_score": 2900,
                                "agent_time_seconds": 1200.4,
                                "timeouts": 1,
                            }
                        ],
                    }
                )
            )
            output = root / "site" / "trials.json"

            count = export_studies_for_site(
                root / "results", output, allow_legacy_protocol=True
            )
            rows = json.loads(output.read_text())

            self.assertEqual(count, 1)
            self.assertEqual(rows[0]["configurationId"], "legacy-study-1")
            self.assertEqual(rows[0]["passRate"], 76)
            self.assertEqual(rows[0]["agentTimeLabel"], "20m 00s")
            self.assertEqual(rows[0]["trial"], 1)
            self.assertEqual(rows[0]["provenance"], "trial")
            self.assertEqual(rows[0]["agentVersion"], "codex-cli test")
            self.assertEqual(rows[0]["corpusRevision"], "abc123")
            self.assertEqual(rows[0]["host"], "test-host")
            self.assertEqual(rows[0]["network"], "offline")

    def test_rejects_studies_without_site_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "study-1" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {"series": "gptTest"},
                        "trials": [{}],
                    }
                )
            )

            with self.assertRaisesRegex(ValueError, "missing site metadata"):
                export_studies_for_site(
                    root, Path(temp) / "out.json", allow_legacy_protocol=True
                )

    def test_ignores_generic_non_site_studies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            generic_path = root / "studies" / "generic" / "summary.json"
            generic_path.parent.mkdir(parents=True)
            generic_path.write_text(
                json.dumps(
                    {
                        "task_count": 1,
                        "metadata": {"solution": "reference"},
                        "trials": [{"run_id": "generic"}],
                    }
                )
            )
            site_path = root / "studies" / "site" / "summary.json"
            site_path.parent.mkdir(parents=True)
            site_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {
                            "label": "GPT Test via Codex CLI",
                            "model": "gpt-test",
                            "series": "gptTest",
                            "effort": "high",
                            "marker": "TH",
                            "kind": "codex",
                            "agent_version": "codex-cli test",
                            "corpus_revision": "abc123",
                            "host": "test-host",
                            "network": "offline",
                        },
                        "trials": [
                            {
                                "run_id": "run-1",
                                "passed_tasks": 22,
                                "failed_tasks": 7,
                                "score": 2200,
                                "max_score": 2900,
                                "agent_time_seconds": 1200,
                                "timeouts": 0,
                            }
                        ],
                    }
                )
            )

            output = Path(temp) / "out.json"
            count = export_studies_for_site(root, output, allow_legacy_protocol=True)

            self.assertEqual(count, 1)
            self.assertEqual(json.loads(output.read_text())[0]["runId"], "run-1")

    def test_ignores_explicitly_unpublished_site_studies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unpublished_path = root / "studies" / "old" / "summary.json"
            unpublished_path.parent.mkdir(parents=True)
            unpublished_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {
                            **self.site_metadata(),
                            "publish": False,
                        },
                        "trials": [self.trial("old-run")],
                    }
                )
            )
            published_path = root / "studies" / "new" / "summary.json"
            published_path.parent.mkdir(parents=True)
            published_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [self.trial("new-run")],
                    }
                )
            )

            output = root / "out.json"
            count = export_studies_for_site(root, output, allow_legacy_protocol=True)

            self.assertEqual(count, 1)
            self.assertEqual(json.loads(output.read_text())[0]["runId"], "new-run")

    def test_publication_gate_rejects_an_incomplete_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "study-1" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {
                            "label": "GPT Test via Codex CLI",
                            "model": "gpt-test",
                            "series": "gptTest",
                            "effort": "high",
                            "marker": "TH",
                            "kind": "codex",
                            "agent_version": "codex-cli test",
                            "corpus_revision": "abc123",
                            "host": "test-host",
                            "network": "offline",
                        },
                        "trials": [
                            {
                                "run_id": "run-1",
                                "passed_tasks": 22,
                                "failed_tasks": 7,
                                "score": 2200,
                                "max_score": 2900,
                                "agent_time_seconds": 1200,
                                "timeouts": 0,
                            }
                        ],
                    }
                )
            )

            with self.assertRaisesRegex(ValueError, "below minimum_trials=5"):
                export_studies_for_site(
                    root,
                    Path(temp) / "out.json",
                    task_count=29,
                    minimum_trials=5,
                    expected_configurations=1,
                    allow_legacy_protocol=True,
                )

    def test_publication_gate_rejects_a_missing_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "study-1" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": {
                            "label": "GPT Test via Codex CLI",
                            "model": "gpt-test",
                            "series": "gptTest",
                            "effort": "high",
                            "marker": "TH",
                            "kind": "codex",
                            "agent_version": "codex-cli test",
                            "corpus_revision": "abc123",
                            "host": "test-host",
                            "network": "offline",
                        },
                        "trials": [
                            {
                                "run_id": f"run-{index}",
                                "passed_tasks": 22,
                                "failed_tasks": 7,
                                "score": 2200,
                                "max_score": 2900,
                                "agent_time_seconds": 1200,
                                "timeouts": 0,
                            }
                            for index in range(5)
                        ],
                    }
                )
            )

            with self.assertRaisesRegex(
                ValueError, "expected 2 configurations, found 1"
            ):
                export_studies_for_site(
                    root,
                    Path(temp) / "out.json",
                    task_count=29,
                    minimum_trials=5,
                    expected_configurations=2,
                    allow_legacy_protocol=True,
                )

    def test_numbers_replicates_across_separate_study_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index, run_id in enumerate(("run-b", "run-a"), start=1):
                summary_path = root / "studies" / f"study-{index}" / "summary.json"
                summary_path.parent.mkdir(parents=True)
                summary_path.write_text(
                    json.dumps(
                        {
                            "task_count": 29,
                            "metadata": self.site_metadata(),
                            "trials": [self.trial(run_id)],
                        }
                    )
                )

            output = root / "out.json"
            export_studies_for_site(root, output, allow_legacy_protocol=True)
            rows = json.loads(output.read_text())

            self.assertEqual([row["runId"] for row in rows], ["run-a", "run-b"])
            self.assertEqual([row["trial"] for row in rows], [1, 1])
            self.assertEqual(
                [row["configurationId"] for row in rows],
                ["legacy-study-2", "legacy-study-1"],
            )

    def test_rejects_duplicate_run_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for index in (1, 2):
                summary_path = root / "studies" / f"study-{index}" / "summary.json"
                summary_path.parent.mkdir(parents=True)
                summary_path.write_text(
                    json.dumps(
                        {
                            "task_count": 29,
                            "metadata": self.site_metadata(),
                            "trials": [self.trial("duplicate-run")],
                        }
                    )
                )

            with self.assertRaisesRegex(ValueError, "duplicate run IDs"):
                export_studies_for_site(
                    root, root / "out.json", allow_legacy_protocol=True
                )

    def test_merges_new_trials_into_existing_site_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first_path = root / "studies" / "first" / "summary.json"
            first_path.parent.mkdir(parents=True)
            first_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [self.trial("run-1")],
                    }
                )
            )
            output = root / "site.json"
            export_studies_for_site(root, output, allow_legacy_protocol=True)

            first = json.loads(first_path.read_text())
            first["metadata"]["publish"] = False
            first_path.write_text(json.dumps(first))
            second_path = root / "studies" / "second" / "summary.json"
            second_path.parent.mkdir(parents=True)
            second_metadata = {**self.site_metadata(), "series": "localModel"}
            second_trial = {**self.trial("run-2"), "agent_time_seconds": 3661}
            second_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": second_metadata,
                        "trials": [second_trial],
                    }
                )
            )

            count = export_studies_for_site(
                root, output, merge_existing=True, allow_legacy_protocol=True
            )
            rows = json.loads(output.read_text())

            self.assertEqual(count, 2)
            self.assertEqual([row["runId"] for row in rows], ["run-1", "run-2"])
            self.assertEqual(rows[1]["agentTimeLabel"], "1h 01m 01s")

    def test_merge_replaces_a_run_when_its_configuration_metadata_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "study" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary = {
                "task_count": 29,
                "metadata": self.site_metadata(),
                "trials": [self.trial("same-run")],
            }
            summary_path.write_text(json.dumps(summary))
            output = root / "site.json"
            export_studies_for_site(root, output, allow_legacy_protocol=True)

            summary["metadata"]["effort"] = "default"
            summary_path.write_text(json.dumps(summary))
            count = export_studies_for_site(
                root, output, merge_existing=True, allow_legacy_protocol=True
            )
            rows = json.loads(output.read_text())

            self.assertEqual(count, 1)
            self.assertEqual(rows[0]["configurationId"], "legacy-study")
            self.assertEqual(rows[0]["runId"], "same-run")

    def test_rejects_legacy_protocol_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "legacy" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [self.trial("legacy-run")],
                    }
                )
            )

            with self.assertRaisesRegex(ValueError, "incomplete legacy protocol"):
                export_studies_for_site(root, root / "out.json")

    def test_exports_stored_content_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "current" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0-dev",
                "corpus_visibility": "public",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_schema_version": 1,
                "protocol_complete": True,
                "completion_attestation": "required",
                "model_identity_evidence": "vendor-api-direct",
                "configuration_id": "cfg-stored",
                "timing_environment_id": "timing-stored",
                "wrapper_prompt_sha256": "b" * 64,
                "agent_command_sha256": "a" * 64,
                "agent_adapter": "codex-json",
                "agent_adapter_sha256": "d" * 64,
                "attestation_trust": "provisional-same-uid",
            }
            trial = {
                **self.trial("current-run"),
                "corpus_digest": "c" * 64,
                "configuration_id": "cfg-stored",
            }
            summary_path.write_text(
                json.dumps(
                    {"task_count": 29, "metadata": metadata, "trials": [trial]}
                )
            )

            export_studies_for_site(root, root / "out.json")
            row = json.loads((root / "out.json").read_text())[0]

            self.assertEqual(row["configurationId"], "cfg-stored")
            self.assertEqual(row["corpusId"], "test-corpus")
            self.assertEqual(row["corpusDigest"], "c" * 64)
            self.assertEqual(row["protocolId"], "test-protocol")
            self.assertEqual(row["timingEnvironmentId"], "timing-stored")
            self.assertNotIn("agentCommand", row)

    def test_legacy_opt_in_preserves_stored_incomplete_identities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "incomplete" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "protocol_complete": False,
                "configuration_id": "cfg-incomplete",
                "corpus_digest": "i" * 64,
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0-dev",
            }
            trial = {
                **self.trial("incomplete-run"),
                "configuration_id": "cfg-incomplete",
                "corpus_digest": "i" * 64,
            }
            summary_path.write_text(
                json.dumps(
                    {"task_count": 29, "metadata": metadata, "trials": [trial]}
                )
            )

            export_studies_for_site(
                root, root / "out.json", allow_legacy_protocol=True
            )
            row = json.loads((root / "out.json").read_text())[0]

            self.assertEqual(row["configurationId"], "cfg-incomplete")
            self.assertEqual(row["corpusDigest"], "i" * 64)
            self.assertFalse(row["protocolComplete"])

    def test_incomplete_stored_identity_must_match_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "incomplete" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "protocol_complete": False,
                "configuration_id": "cfg-incomplete",
                "corpus_digest": "i" * 64,
            }
            trial = {
                **self.trial("incomplete-run"),
                "configuration_id": "cfg-other",
                "corpus_digest": "i" * 64,
            }
            summary_path.write_text(
                json.dumps(
                    {"task_count": 29, "metadata": metadata, "trials": [trial]}
                )
            )

            with self.assertRaisesRegex(ValueError, "mixed corpus or protocol"):
                export_studies_for_site(
                    root, root / "out.json", allow_legacy_protocol=True
                )

    def test_rejects_mixed_trial_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "mixed" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0-dev",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_complete": True,
                "completion_attestation": "required",
                "configuration_id": "cfg-stored",
                "timing_environment_id": "timing-stored",
                "wrapper_prompt_sha256": "b" * 64,
                "agent_command_sha256": "a" * 64,
                "agent_adapter": "codex-json",
                "agent_adapter_sha256": "d" * 64,
                "attestation_trust": "provisional-same-uid",
            }
            trial = {
                **self.trial("mixed-run"),
                "corpus_digest": "d" * 64,
                "configuration_id": "cfg-stored",
            }
            summary_path.write_text(
                json.dumps(
                    {"task_count": 29, "metadata": metadata, "trials": [trial]}
                )
            )

            with self.assertRaisesRegex(ValueError, "mixed corpus or protocol"):
                export_studies_for_site(root, root / "out.json")

    def test_complete_protocol_requires_derived_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "current" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0-dev",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_complete": True,
                "completion_attestation": "required",
                "configuration_id": "cfg-stored",
                "timing_environment_id": "timing-stored",
            }
            trial = {
                **self.trial("current-run"),
                "corpus_digest": "c" * 64,
                "configuration_id": "cfg-stored",
            }
            summary_path.write_text(
                json.dumps(
                    {"task_count": 29, "metadata": metadata, "trials": [trial]}
                )
            )

            with self.assertRaisesRegex(ValueError, "wrapper_prompt_sha256"):
                export_studies_for_site(root, root / "out.json")

    def test_current_publication_rejects_legacy_scoring_without_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "current" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            metadata = {
                **self.site_metadata(),
                "corpus_id": "test-corpus",
                "corpus_version": "2.0.0",
                "corpus_digest": "c" * 64,
                "protocol_id": "test-protocol",
                "protocol_complete": True,
                "completion_attestation": "required",
                "configuration_id": "cfg-stored",
                "timing_environment_id": "timing-stored",
                "wrapper_prompt_sha256": "b" * 64,
                "agent_command_sha256": "a" * 64,
                "agent_adapter": "codex-json",
                "agent_adapter_sha256": "d" * 64,
                "attestation_trust": "provisional-same-uid",
            }
            trial = {
                **self.trial("legacy-score"),
                "scoring_schema": "legacy-binary",
                "corpus_digest": "c" * 64,
                "configuration_id": "cfg-stored",
            }
            summary_path.write_text(
                json.dumps({"task_count": 29, "metadata": metadata, "trials": [trial]})
            )

            with self.assertRaisesRegex(ValueError, "legacy scoring"):
                export_studies_for_site(root, root / "out.json")

            self.assertEqual(
                export_studies_for_site(
                    root, root / "legacy.json", allow_legacy_protocol=True
                ),
                1,
            )

    def test_publication_rejects_an_invalid_trial_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            summary_path = root / "studies" / "invalid" / "summary.json"
            summary_path.parent.mkdir(parents=True)
            trial = {**self.trial("invalid-run"), "measurement_status": "invalid"}
            summary_path.write_text(
                json.dumps(
                    {
                        "task_count": 29,
                        "metadata": self.site_metadata(),
                        "trials": [trial],
                    }
                )
            )

            with self.assertRaisesRegex(ValueError, "invalid or incomplete trial"):
                export_studies_for_site(
                    root, root / "out.json", allow_legacy_protocol=True
                )

    @staticmethod
    def site_metadata() -> dict[str, str]:
        return {
            "label": "GPT Test via Codex CLI",
            "model": "gpt-test",
            "series": "gptTest",
            "effort": "high",
            "marker": "TH",
            "kind": "codex",
            "agent_version": "codex-cli test",
            "corpus_revision": "abc123",
            "host": "test-host",
            "network": "offline",
        }

    @staticmethod
    def trial(run_id: str) -> dict[str, object]:
        return {
            "run_id": run_id,
            "passed_tasks": 22,
            "failed_tasks": 7,
            "score": 2200,
            "max_score": 2900,
            "agent_time_seconds": 1200,
            "timeouts": 0,
            "scoring_schema": "criteria-v2",
        }


if __name__ == "__main__":
    unittest.main()
