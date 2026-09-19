# Scoring

Current NixBench tasks declare objective binary criteria in `metadata.toml`.
Each criterion has a stable ID, point value, required flag, and failure class.
The points must sum exactly to the task's `max_score`.

```toml
[[criteria]]
id = "preserves-runtime-inputs"
points = 25
required = true
failure_class = "wrong-value"
```

Evaluators write a schema-2 payload to the evaluator-only
`$NIXBENCH_SCORE_FILE` path:

```json
{
  "schema_version": 2,
  "criteria": {
    "evaluates": true,
    "preserves-runtime-inputs": false
  },
  "notes": ["runtime input preservation check failed"]
}
```

The criterion keys must exactly match task metadata, and each value must be a
JSON boolean. Evaluators do not submit totals or failure classes. The harness
computes both from metadata. Notes are bounded diagnostics and cannot change a
score.

An evaluator exits `0` only when every required criterion passes. Exit `1`
rejects the candidate and may retain partial credit. A disagreement between
the exit code and required criteria makes the measurement invalid.

## Measurement validity and task outcome

`measurement_status` records whether the run measured the candidate:

- `valid` means the evaluator, score payload, agent process, and any required
  completion attestation were usable.
- `invalid` means an evaluator, process, transport, score, or attestation
  failure prevented measurement.
- `incomplete` means a study attempt stopped before it ran the selected task
  set.

For valid measurements, `task_outcome` is `pass`, `fail`, or `agent-timeout`.
The harness records its own timeout event, so an attested agent timeout is a
valid outcome. Evaluator timeouts, evaluator exit codes `2` or greater,
malformed score payloads, non-timeout agent process errors, and missing or
failed required attestations are invalid measurements. Invalid and incomplete
attempts stay in the study `attempts` ledger but never enter `trials`, score
denominators, or estimates.

## Failure classes

Task metadata may use these controlled classes:

- `syntax`
- `evaluation`
- `missing-attr`
- `wrong-value`
- `unavailable-helper`
- `impurity`
- `overfit`
- `maintainability`
- `formatting`

Optional criteria are limited to objective `maintainability` or `formatting`
checks. Infrastructure events do not use these classes.

## Compatibility

The harness can read historical scalar score files for legacy tasks and marks
them `legacy-binary`. Current publishable corpus releases require
`criteria-v2`. `export-site` accepts legacy scoring only with the explicit
`--allow-legacy-protocol` compatibility flag. Historical binary scores are not
converted and must not be pooled with rubric-scored trials.

## Study observations

Study schema version 3 retains one normalized observation for every task in
every valid trial. The primitive evidence is the task identity and digest,
controlled category and difficulty, criterion booleans plus their rubric points,
required flags and failure classes, timeout state, measurement status, task
outcome, infrastructure events, and agent and evaluator durations. `score` and
`max_score` are checked against that rubric evidence.

`normalized_score` is redundant: the shared current-study validator recomputes
it as `score / max_score` (with a documented `1e-12` floating-point tolerance)
and requires the stored value to agree and remain in `[0, 1]`. The same
validator derives pass state from required criteria and timeout state, derives
passed/failed criterion lists and failure classes, and derives every trial's
score, maximum score, score rate, pass/fail counts, task count, timeout count,
and timing totals. Current reporting and publication reject an altered
`normalized_score`, impossible score, duplicate task cell, criterion/pass
disagreement, or redundant trial total rather than using it.

Historical study summaries are hydrated from their referenced run summaries
when those files remain available. A historical summary without those files is
marked `aggregate_only = true`. This is an explicit legacy path: historical
aggregate-only data is never upgraded into a current schema-3 publication by
filling defaults or inventing task observations. Reports do not infer task
observations from a corpus total.

## Reported estimands

`nixbench.reporting` is the canonical implementation for new statistical
reports. Reports define three score summaries:

- Macro task score averages each task's normalized score over valid trials,
  then averages those task means without task weights.
- Macro pass rate applies the same calculation to each task's binary pass
  outcome.
- Point-weighted score divides all earned points by all available points in
  the included task-trial cells.

Reports never pool task-trial cells first when calculating a macro result.
They publish the task count, valid observation count, trial count, raw points,
range, invalid-attempt count, timeout rate where applicable, and exclusion
reasons beside the estimates. Category and difficulty groups contain no
editorial weights. Groups with fewer than five tasks have
`descriptive_only = true` and no task-resampling interval.

## Uncertainty methods

The `student-t-fixed-corpus-run-variation` method estimates the mean statistic
from hypothetical independent repetitions of the same fixed corpus under the
same correctness configuration. It assumes the repeated-trial statistic is
approximately normal. The report retains raw interval bounds. It may also
provide bounds clipped to the display range as separate values. One trial has
no interval, and fewer than five trials produces a warning.

This interval does not estimate a single future-run prediction interval,
evaluator correctness, representativeness of all Nix work, model identity
certainty, or a direct significance test between configurations.

The `wilson-task-pass-stability` method reports per-task pass stability over
valid repeated observations within one correctness configuration. Corpus
health reports keep these intervals separated by configuration. Their pooled
empirical pass rate is descriptive only and does not receive a Wilson interval.
Criterion and failure-class reports use raw numerators and denominators rather
than intervals for small samples.

Task discrimination uses the point-biserial correlation between the binary
task outcome and the sum of the other valid normalized task scores in the same
trial. Sample-size and configuration-diversity thresholds are reapplied after
rows without a leave-one-task-out score are excluded.

The `trial-task-resampling-sensitivity` method measures sensitivity to the
observed trial and fixed-corpus task composition. It requires a complete
rectangular matrix for one corpus and configuration and never imputes missing
cells. Each of 10,000 replicates samples trial indices with replacement, then
samples task IDs with replacement and computes the macro normalized score. The
seed is the SHA-256 digest of the corpus ID, configuration ID, stratum ID, and
method version. Bounds use linear interpolation equivalent to Hyndman-Fan type
7. This is a sensitivity interval, not evidence of generalization to all Nix
work.

Timing summaries are grouped by `timing_environment_id`. A correctness
configuration with more than one timing environment receives separate timing
results and no combined timing interval.
