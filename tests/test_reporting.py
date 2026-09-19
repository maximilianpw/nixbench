from __future__ import annotations

import ast
import json
import tempfile
import unittest
from pathlib import Path

from nixbench.reporting import (
    build_configuration_report,
    build_corpus_health_report,
    build_study_report,
    fixed_corpus_interval,
    load_study_summary,
    resampling_sensitivity,
    wilson_interval,
)


def observation(
    task_id: str,
    *,
    score: float,
    max_score: float = 100,
    passed: bool | None = None,
    category: str = "packages",
    difficulty: str = "medium",
    failed_criteria: list[str] | None = None,
    failure_classes: list[str] | None = None,
    agent_timeout: bool = False,
) -> dict[str, object]:
    normalized = score / max_score
    if passed is None:
        passed = score == max_score
    failed = failed_criteria or ([] if passed else ["behavior"])
    return {
        "task_id": task_id,
        "task_digest": f"digest-{task_id}",
        "category": category,
        "difficulty": difficulty,
        "measurement_status": "valid",
        "task_outcome": "pass" if passed else "fail",
        "passed": passed,
        "score": score,
        "max_score": max_score,
        "normalized_score": normalized,
        "passed_criteria": [] if failed else ["behavior"],
        "failed_criteria": failed,
        "failure_classes": failure_classes or ([] if passed else ["wrong-value"]),
        "agent_duration_seconds": 2.0,
        "evaluator_duration_seconds": 0.25,
        "agent_timeout": agent_timeout,
        "infrastructure_events": [],
    }


def trial(run_id: str, observations: list[dict[str, object]]) -> dict[str, object]:
    score = sum(float(item["score"]) for item in observations)
    max_score = sum(float(item["max_score"]) for item in observations)
    passed_tasks = sum(bool(item["passed"]) for item in observations)
    agent_time = sum(float(item["agent_duration_seconds"]) for item in observations)
    return {
        "run_id": run_id,
        "created_at": "2026-09-16T00:00:00+00:00",
        "passed_tasks": passed_tasks,
        "failed_tasks": len(observations) - passed_tasks,
        "task_count": len(observations),
        "score": score,
        "max_score": max_score,
        "score_rate": score / max_score,
        "agent_time_seconds": agent_time,
        "agent_seconds_per_task": agent_time / len(observations),
        "timeouts": 0,
        "scoring_schema": "criteria-v2",
        "corpus_digest": "corpus-a",
        "configuration_id": "cfg-a",
        "observations": observations,
    }


class ReportingTests(unittest.TestCase):
    def test_reporting_module_has_no_production_assertions(self) -> None:
        source_path = Path(__file__).parents[1] / "nixbench" / "reporting.py"
        tree = ast.parse(source_path.read_text())

        self.assertEqual(
            [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Assert)],
            [],
        )

    def test_fixed_corpus_interval_keeps_raw_and_display_bounds(self) -> None:
        result = fixed_corpus_interval(
            [-0.1, 0.2],
            included_ids=["run-a", "run-b"],
            display_bounds=(0.0, 1.0),
        )

        self.assertEqual(result["method"], "student-t-fixed-corpus-run-variation")
        self.assertEqual(result["method_version"], "1")
        self.assertEqual(result["sampling_unit"], "complete-corpus-trial")
        self.assertEqual(result["n"], 2)
        self.assertLess(result["interval"]["raw_low"], 0)
        self.assertEqual(result["interval"]["display_low"], 0.0)
        self.assertIn("fewer-than-five-trials", result["warnings"])

    def test_fixed_corpus_single_trial_has_no_interval(self) -> None:
        result = fixed_corpus_interval([0.75], included_ids=["run-a"])

        self.assertIsNone(result["interval"])
        self.assertIn("interval-requires-at-least-two-trials", result["warnings"])

    def test_fixed_corpus_large_sample_keeps_a_student_t_critical_value(self) -> None:
        values = [float(index) for index in range(32)]
        result = fixed_corpus_interval(
            values,
            included_ids=[f"run-{index}" for index in range(32)],
        )
        implied_critical = (
            result["interval"]["margin"]
            * (32**0.5)
            / result["standard_deviation"]
        )

        self.assertGreater(implied_critical, 1.96)

    def test_wilson_interval_matches_hand_calculated_fixture(self) -> None:
        result = wilson_interval(4, 10, included_ids=[f"run-{index}" for index in range(10)])

        self.assertEqual(result["method"], "wilson-task-pass-stability")
        self.assertAlmostEqual(result["estimate"], 0.4)
        self.assertAlmostEqual(result["interval"]["low"], 0.1681803297, places=9)
        self.assertAlmostEqual(result["interval"]["high"], 0.6873262303, places=9)

    def test_resampling_is_deterministic_and_identity_seeded(self) -> None:
        trials = [
            trial(
                f"run-{run}",
                [
                    observation(f"task-{task}", score=(run * 10 + task * 5) % 101)
                    for task in range(5)
                ],
            )
            for run in range(4)
        ]

        first = resampling_sensitivity(
            trials,
            task_ids=[f"task-{task}" for task in range(5)],
            corpus_id="corpus-a",
            configuration_id="cfg-a",
            stratum_id="whole-corpus",
        )
        repeated = resampling_sensitivity(
            trials,
            task_ids=[f"task-{task}" for task in range(5)],
            corpus_id="corpus-a",
            configuration_id="cfg-a",
            stratum_id="whole-corpus",
        )
        different_identity = resampling_sensitivity(
            trials,
            task_ids=[f"task-{task}" for task in range(5)],
            corpus_id="corpus-a",
            configuration_id="cfg-b",
            stratum_id="whole-corpus",
        )

        self.assertEqual(first, repeated)
        self.assertEqual(first["replicates"], 10_000)
        self.assertEqual(first["interval"], {"level": 0.95, "low": 0.125, "high": 0.375})
        self.assertNotEqual(first["seed_sha256"], different_identity["seed_sha256"])

    def test_resampling_rejects_an_incomplete_matrix_without_imputation(self) -> None:
        trials = [
            trial("run-a", [observation(f"task-{index}", score=100) for index in range(5)]),
            trial("run-b", [observation(f"task-{index}", score=50) for index in range(4)]),
        ]

        result = resampling_sensitivity(
            trials,
            task_ids=[f"task-{index}" for index in range(5)],
            corpus_id="corpus-a",
            configuration_id="cfg-a",
            stratum_id="whole-corpus",
        )

        self.assertIsNone(result["interval"])
        self.assertEqual(result["unavailable_reason"], "incomplete-rectangular-matrix")
        self.assertIn("run-b/task-4", result["excluded_ids"])

    def test_study_report_distinguishes_macro_and_point_weighted_scores(self) -> None:
        first = trial(
            "run-a",
            [
                observation("small", score=100, max_score=100, category="fetchers"),
                observation(
                    "large",
                    score=0,
                    max_score=900,
                    category="packages",
                    agent_timeout=True,
                ),
            ],
        )
        second = trial(
            "run-b",
            [
                observation("small", score=100, max_score=100, category="fetchers"),
                observation("large", score=900, max_score=900, category="packages"),
            ],
        )
        study = {
            "schema_version": 3,
            "study_id": "study-a",
            "metadata": {
                "corpus_id": "corpus-a",
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
                "timing_environment_id": "timing-a",
            },
            "trial_count": 2,
            "task_count": 2,
            "trials": [first, second],
            "attempts": [],
        }

        report = build_study_report(study)
        whole = report["strata"]["whole_corpus"]

        self.assertEqual(report["schema_version"], 1)
        self.assertFalse(report["aggregate_only"])
        self.assertAlmostEqual(whole["macro_task_score"], 0.75)
        self.assertAlmostEqual(whole["point_weighted_score"], 0.55)
        self.assertAlmostEqual(whole["macro_pass_rate"], 0.75)
        self.assertTrue(whole["descriptive_only"])
        self.assertEqual(whole["task_count"], 2)
        self.assertEqual(whole["valid_observation_count"], 4)
        self.assertEqual(whole["timeout_count"], 1)
        self.assertEqual(whole["timeout_rate"], 0.25)
        self.assertEqual(report["timing"][0]["timing_environment_id"], "timing-a")

    def test_study_report_counts_invalid_attempts_and_reasons(self) -> None:
        complete = trial("run-a", [observation("task-a", score=100)])
        study = {
            "schema_version": 3,
            "study_id": "study-a",
            "metadata": {
                "corpus_id": "corpus-a",
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
            },
            "trial_count": 1,
            "task_count": 1,
            "trials": [complete],
            "attempt_count": 2,
            "attempts": [
                {"run_id": "run-a", "measurement_status": "valid", "exclusion_reasons": []},
                {
                    "run_id": "run-b",
                    "measurement_status": "invalid",
                    "exclusion_reasons": ["evaluator-timeout"],
                    "tasks": [
                        {
                            "task_id": "task-a",
                            "category": "packages",
                            "difficulty": "medium",
                            "measurement_status": "valid",
                            "invalid_reason": "evaluator-timeout",
                        },
                        {
                            "task_id": "task-b",
                            "category": "packages",
                            "difficulty": "medium",
                            "measurement_status": "invalid",
                            "invalid_reason": "evaluator-timeout",
                        }
                    ],
                },
            ],
        }

        report = build_study_report(study)

        self.assertEqual(report["attempts"]["invalid_count"], 1)
        self.assertEqual(report["attempts"]["invalid_rate"], 0.5)
        self.assertEqual(report["attempts"]["reasons"], {"evaluator-timeout": 1})
        self.assertEqual(report["strata"]["whole_corpus"]["invalid_attempt_count"], 1)
        self.assertEqual(report["attempts"]["by_task"].get("task-a", 0), 0)

    def test_run_variation_excludes_an_incomplete_task_row(self) -> None:
        task_ids = [f"task-{index}" for index in range(5)]
        complete = trial(
            "run-a", [observation(task_id, score=100) for task_id in task_ids]
        )
        incomplete = trial(
            "run-b", [observation(task_id, score=50) for task_id in task_ids[:-1]]
        )
        study = {
            "schema_version": 3,
            "study_id": "incomplete-matrix",
            "metadata": {
                "corpus_id": "corpus-a",
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
            },
            "trials": [complete, incomplete],
            "attempts": [],
        }

        report = build_study_report(study)
        interval = report["strata"]["whole_corpus"]["run_variation"]

        self.assertEqual(interval["n"], 1)
        self.assertEqual(
            interval["exclusion_reasons"], {"run-b": "incomplete-task-row"}
        )

    def test_historical_study_hydrates_from_run_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp)
            study_path = results / "studies" / "old" / "summary.json"
            study_path.parent.mkdir(parents=True)
            study_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "study_id": "old",
                        "metadata": {
                            "corpus_task_digests": {"task-a": "digest-task-a"}
                        },
                        "trial_count": 1,
                        "task_count": 1,
                        "trials": [
                            {
                                "run_id": "run-a",
                                "passed_tasks": 1,
                                "failed_tasks": 0,
                                "task_count": 1,
                                "score": 100,
                                "max_score": 100,
                                "score_rate": 1,
                                "agent_time_seconds": 2,
                                "agent_seconds_per_task": 2,
                                "timeouts": 0,
                            }
                        ],
                    }
                )
            )
            run_path = results / "run-a" / "summary.json"
            run_path.parent.mkdir(parents=True)
            run_path.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "task_id": "task-a",
                                "category": "packages",
                                "difficulty": "medium",
                                "measurement_status": "valid",
                                "task_outcome": "pass",
                                "passed": True,
                                "score": 100,
                                "max_score": 100,
                                "criteria": {"behavior": True},
                                "failure_classes": [],
                                "infrastructure_events": [],
                                "agent": {"duration_seconds": 2, "timed_out": False},
                                "check": {"duration_seconds": 0.25},
                            }
                        ]
                    }
                )
            )

            loaded = load_study_summary(study_path)

            self.assertFalse(loaded["aggregate_only"])
            self.assertEqual(loaded["trials"][0]["observations"][0]["task_id"], "task-a")
            self.assertEqual(
                loaded["trials"][0]["observations"][0]["task_digest"],
                "digest-task-a",
            )

    def test_pre_plan_four_run_summary_falls_back_to_aggregate_only(self) -> None:
        fixture = (
            Path(__file__).parent
            / "fixtures"
            / "studies"
            / "legacy-pre-plan-004"
            / "summary.json"
        )

        loaded = load_study_summary(fixture)

        self.assertTrue(loaded["aggregate_only"])
        self.assertNotIn("observations", loaded["trials"][0])

    def test_hydration_total_mismatch_falls_back_to_aggregate_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            results = Path(temp)
            study_path = results / "studies" / "old" / "summary.json"
            study_path.parent.mkdir(parents=True)
            study_path.write_text(
                json.dumps(
                    {
                        "study_id": "old",
                        "metadata": {},
                        "task_count": 1,
                        "trials": [
                            {
                                "run_id": "run-a",
                                "passed_tasks": 0,
                                "score": 99,
                                "max_score": 100,
                                "timeouts": 0,
                            }
                        ],
                    }
                )
            )
            run_path = results / "run-a" / "summary.json"
            run_path.parent.mkdir(parents=True)
            run_path.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "task_id": "task-a",
                                "category": "packages",
                                "difficulty": "medium",
                                "measurement_status": "valid",
                                "task_outcome": "pass",
                                "passed": True,
                                "score": 100,
                                "max_score": 100,
                                "criteria": {"behavior": True},
                                "failure_classes": [],
                                "infrastructure_events": [],
                                "agent": {"duration_seconds": 1, "timed_out": False},
                                "check": {"duration_seconds": 0.1},
                            }
                        ]
                    }
                )
            )

            loaded = load_study_summary(study_path)

        self.assertTrue(loaded["aggregate_only"])
        self.assertNotIn("observations", loaded["trials"][0])

    def test_historical_study_without_runs_is_aggregate_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "studies" / "old" / "summary.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps(
                    {
                        "study_id": "old",
                        "metadata": {},
                        "trial_count": 1,
                        "task_count": 1,
                        "trials": [{"run_id": "missing"}],
                    }
                )
            )

            loaded = load_study_summary(path)
            report = build_study_report(loaded)

            self.assertTrue(loaded["aggregate_only"])
            self.assertTrue(report["aggregate_only"])
            self.assertIsNone(report["strata"])

    def test_corpus_health_orders_tasks_and_gates_discrimination(self) -> None:
        task_evidence = [
            {
                "task_id": task_id,
                "category": "packages",
                "difficulty": "medium",
                "reference_full_score": True,
                "starter_rejected": True,
                "pass_fixture_count": 1,
                "reject_fixture_count": 2,
                "criterion_coverage": ["behavior"],
                "criterion_ids": ["behavior"],
                "evaluator_deterministic": True,
                "evaluator_durations_seconds": [0.1, 0.2],
            }
            for task_id in ("task-b", "task-a")
        ]
        study = {
            "schema_version": 3,
            "study_id": "study-a",
            "metadata": {
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
            },
            "trials": [
                trial(
                    f"run-{index}",
                    [
                        observation("task-a", score=100 if index % 2 else 0),
                        observation("task-b", score=100),
                    ],
                )
                for index in range(4)
            ],
            "attempts": [],
        }

        report = build_corpus_health_report(
            corpus_digest="corpus-a",
            task_evidence=task_evidence,
            studies=[study],
            discrimination_min_observations=20,
            discrimination_min_configurations=2,
        )

        self.assertEqual(list(report["tasks"]), ["task-a", "task-b"])
        self.assertEqual(
            report["tasks"]["task-a"]["discrimination"]["unavailable_reason"],
            "insufficient-sample-size",
        )
        self.assertEqual(report["tasks"]["task-a"]["author_difficulty"], "medium")
        self.assertIsNotNone(report["tasks"]["task-a"]["empirical_solve_rate_band"])
        self.assertNotIn("pass_stability", report["tasks"]["task-a"])
        self.assertIn(
            "cfg-a", report["tasks"]["task-a"]["pass_stability_by_configuration"]
        )

    def test_configuration_report_separates_timing_environments(self) -> None:
        studies = []
        for index, timing_environment in enumerate(("timing-a", "timing-b")):
            studies.append(
                {
                    "schema_version": 3,
                    "study_id": f"study-{index}",
                    "metadata": {
                        "corpus_id": "corpus-a",
                        "corpus_digest": "corpus-a",
                        "configuration_id": "cfg-a",
                        "timing_environment_id": timing_environment,
                    },
                    "task_count": 1,
                    "trials": [
                        trial(
                            f"run-{index}",
                            [observation("task-a", score=100)],
                        )
                    ],
                    "attempts": [],
                }
            )

        report = build_configuration_report(studies)

        self.assertEqual(
            [item["timing_environment_id"] for item in report["timing"]],
            ["timing-a", "timing-b"],
        )
        self.assertIsNone(report["combined_timing_interval"])
        self.assertIn("multiple-timing-environments", report["warnings"])

    def test_corpus_health_computes_discrimination_when_thresholds_are_met(self) -> None:
        evidence = [
            {
                "task_id": "task-a",
                "category": "packages",
                "difficulty": "hard",
                "reference_full_score": True,
                "starter_rejected": True,
                "pass_fixture_count": 1,
                "reject_fixture_count": 1,
                "criterion_coverage": ["behavior"],
                "criterion_ids": ["behavior"],
                "evaluator_deterministic": True,
                "evaluator_durations_seconds": [0.1, 0.2],
            }
        ]
        studies = []
        for configuration in ("cfg-a", "cfg-b"):
            trials = []
            for index in range(10):
                solved = index >= 5
                trials.append(
                    trial(
                        f"{configuration}-run-{index}",
                        [
                            observation("task-a", score=100 if solved else 0, passed=solved),
                            observation("task-b", score=90 if solved else 10, passed=solved),
                        ],
                    )
                )
            studies.append(
                {
                    "metadata": {
                        "corpus_digest": "corpus-a",
                        "configuration_id": configuration,
                    },
                    "trials": trials,
                    "attempts": [],
                }
            )

        report = build_corpus_health_report(
            corpus_digest="corpus-a",
            task_evidence=evidence,
            studies=studies,
            discrimination_min_observations=20,
            discrimination_min_configurations=2,
        )

        discrimination = report["tasks"]["task-a"]["discrimination"]
        self.assertIsNone(discrimination["unavailable_reason"])
        self.assertAlmostEqual(discrimination["estimate"], 1.0)
        self.assertEqual(
            discrimination["leave_one_task_out_statistic"],
            "sum-normalized-task-scores",
        )

    def test_discrimination_rechecks_threshold_after_leave_one_out_filtering(self) -> None:
        evidence = [
            {
                "task_id": "task-a",
                "category": "packages",
                "difficulty": "medium",
                "reference_full_score": True,
                "starter_rejected": True,
                "pass_fixture_count": 1,
                "reject_fixture_count": 1,
                "criterion_ids": ["behavior"],
                "criterion_coverage": ["behavior"],
                "evaluator_deterministic": True,
                "evaluator_durations_seconds": [],
            }
        ]
        studies = []
        for configuration in ("cfg-a", "cfg-b"):
            values = []
            for index in range(10):
                observations = [observation("task-a", score=100 if index % 2 else 0)]
                if not (configuration == "cfg-b" and index == 9):
                    observations.append(observation("task-b", score=index * 10))
                values.append(trial(f"{configuration}-{index}", observations))
            studies.append(
                {
                    "metadata": {
                        "corpus_digest": "corpus-a",
                        "configuration_id": configuration,
                    },
                    "trials": values,
                    "attempts": [],
                }
            )

        report = build_corpus_health_report(
            corpus_digest="corpus-a",
            task_evidence=evidence,
            studies=studies,
            discrimination_min_observations=20,
            discrimination_min_configurations=2,
        )
        discrimination = report["tasks"]["task-a"]["discrimination"]

        self.assertEqual(discrimination["n"], 19)
        self.assertEqual(
            discrimination["unavailable_reason"], "insufficient-sample-size"
        )

    def test_health_invalid_counts_use_row_status_and_missing_tasks(self) -> None:
        evidence = [
            {
                "task_id": task_id,
                "category": "packages",
                "difficulty": "medium",
                "reference_full_score": True,
                "starter_rejected": True,
                "pass_fixture_count": 1,
                "reject_fixture_count": 1,
                "criterion_ids": [],
                "criterion_coverage": [],
                "evaluator_deterministic": True,
                "evaluator_durations_seconds": [],
            }
            for task_id in ("task-a", "task-b", "task-c")
        ]
        study = {
            "metadata": {"corpus_digest": "corpus-a", "configuration_id": "cfg-a"},
            "trials": [],
            "attempts": [
                {
                    "measurement_status": "invalid",
                    "tasks": [
                        {"task_id": "task-a", "measurement_status": "valid"},
                        {"task_id": "task-b", "measurement_status": "invalid"},
                    ],
                }
            ],
        }

        report = build_corpus_health_report(
            corpus_digest="corpus-a", task_evidence=evidence, studies=[study]
        )

        self.assertEqual(report["tasks"]["task-a"]["invalid_measurement_count"], 0)
        self.assertEqual(report["tasks"]["task-b"]["invalid_measurement_count"], 1)
        self.assertEqual(report["tasks"]["task-c"]["invalid_measurement_count"], 1)

    def test_configuration_report_keeps_observations_beside_aggregate_sibling(self) -> None:
        observed_study = {
            "study_id": "observed",
            "task_count": 1,
            "metadata": {
                "corpus_id": "corpus-a",
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
            },
            "trials": [trial("run-observed", [observation("task-a", score=75)])],
            "attempts": [],
        }
        aggregate_study = {
            "study_id": "aggregate",
            "task_count": 1,
            "metadata": {
                "corpus_id": "corpus-a",
                "corpus_digest": "corpus-a",
                "configuration_id": "cfg-a",
            },
            "aggregate_only": True,
            "trials": [{"run_id": "run-aggregate", "score": 100}],
            "attempts": [],
        }

        report = build_configuration_report([observed_study, aggregate_study])

        self.assertFalse(report["aggregate_only"])
        self.assertEqual(
            report["strata"]["whole_corpus"]["macro_task_score"], 0.75
        )
        self.assertEqual(
            report["excluded_trials"],
            [
                {
                    "study_id": "aggregate",
                    "run_id": "run-aggregate",
                    "reason": "task-observations-unavailable",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
