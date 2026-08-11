from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from nixbench.export import export_studies_for_site


class ExportTests(unittest.TestCase):
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

            count = export_studies_for_site(root / "results", output)
            rows = json.loads(output.read_text())

            self.assertEqual(count, 1)
            self.assertEqual(rows[0]["configurationId"], "gptTest-high-29")
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
                export_studies_for_site(root, Path(temp) / "out.json")

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
            count = export_studies_for_site(root, output)

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
            count = export_studies_for_site(root, output)

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
            export_studies_for_site(root, output)
            rows = json.loads(output.read_text())

            self.assertEqual([row["runId"] for row in rows], ["run-a", "run-b"])
            self.assertEqual([row["trial"] for row in rows], [1, 2])

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
                export_studies_for_site(root, root / "out.json")

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
            export_studies_for_site(root, output)

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

            count = export_studies_for_site(root, output, merge_existing=True)
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
            export_studies_for_site(root, output)

            summary["metadata"]["effort"] = "default"
            summary_path.write_text(json.dumps(summary))
            count = export_studies_for_site(root, output, merge_existing=True)
            rows = json.loads(output.read_text())

            self.assertEqual(count, 1)
            self.assertEqual(rows[0]["configurationId"], "gptTest-default-29")
            self.assertEqual(rows[0]["runId"], "same-run")

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
        }


if __name__ == "__main__":
    unittest.main()
