# Plan 012: Enforce task calibration before corpus activation

> **Executor instructions**: Follow this plan step by step. This plan defines
> release policy and machine gates; it does not authorize spending money on
> model runs or publishing results. Run every local verification command. Stop
> on any policy ambiguity listed below. Update `plans/README.md` when complete
> unless a reviewer owns the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- corpus docs/benchmark-governance.md docs/authoring.md docs/reproducibility.md nixbench/release.py nixbench/reporting.py nixbench/cli.py tests/test_release.py tests/test_reporting.py tests/test_cli.py`
> This plan assumes Plans 009 and 011 have landed so calibration consumes strict
> studies and the final evaluator contracts.

## Status

- **Priority**: P1
- **Effort**: L
- **Risk**: MED
- **Depends on**: `plans/009-strict-study-publication-validation.md`, `plans/011-harden-criterion-contracts.md`
- **Category**: tech-debt
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

Governance says tasks are calibrated before activation across at least three
materially different configurations, but the current release gate checks only
structural evaluator health. The current-corpus health report contains zero
empirical observations and 2.0.0 still reports eligible. Without enforced
calibration, author difficulty, discrimination, timeout suitability, and
failure behavior remain unverified while the corpus is labeled active.

## Current state

- `docs/benchmark-governance.md:76-84` requires pre-activation review of solve
  rates, uncertainty, timeout/invalid rates, discrimination, disputes,
  alternatives, and empirical difficulty.
- `corpus/task-lifecycle.toml` currently contains only:

  ```toml
  schema_version = 1
  quarantined_tasks = []
  ```

- `nixbench/release.py:90-277` gates structure, references, starters, fixtures,
  determinism, runtime margin, known issues, lifecycle-file validity, release
  note, and manifest—but not calibration evidence.
- `nixbench/reporting.py` already computes per-task pass stability,
  discrimination with minimum sample/configuration thresholds, timeout rates,
  and empirical solve-rate bands. Reuse these canonical outputs.
- Corpus categories with fewer than five tasks are already marked descriptive
  only. Calibration must not pretend that small strata generalize to all Nix
  work.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Release/report tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_release tests.test_reporting tests.test_cli -v` | all pass |
| Corpus health | `PYTHONDONTWRITEBYTECODE=1 python3 bench.py corpus-health --studies-dir results/studies --output /tmp/nixbench-health.json` | writes schema-valid report |
| Release check | `CI=1 PYTHONDONTWRITEBYTECODE=1 python3 bench.py release-check --corpus-root . --json` | fails while required calibration is absent; passes only with approved evidence or calibrating state |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | exit 0 with system tools |

## Scope

**In scope**:
- `corpus/task-lifecycle.toml` schema/version
- A new versioned calibration registry under `corpus/`, if appropriate
- `nixbench/release.py`
- `nixbench/reporting.py` only for reusable calibration summaries
- `nixbench/cli.py`
- `tests/test_release.py`
- `tests/test_reporting.py`
- `tests/test_cli.py`
- `docs/benchmark-governance.md`
- `docs/authoring.md`
- `docs/reproducibility.md`
- Release note/manifest updates required by governance

**Out of scope**:
- Actually running paid calibration configurations without explicit operator
  authorization.
- Automatically promoting or quarantining tasks based solely on model scores.
- Changing author difficulty automatically.
- Category reweighting.
- Building the first private held-out task set.

## Git workflow

- Suggested branch: `advisor/012-enforce-calibration-before-activation`
- Suggested commits: lifecycle/calibration schema, release gates/tests, docs and
  release metadata.
- Do not run paid agents, publish results, or activate a private corpus.

## Steps

### Step 1: Define explicit lifecycle and calibration schemas

Replace the quarantine-only lifecycle file with a versioned per-task registry,
or add a separate calibration registry if that yields a deeper module. Every
active task needs an explicit lifecycle state from the documented vocabulary:

- `draft`
- `calibrating`
- `active`
- `quarantined`
- `deprecated`
- `retired`

For calibration records, store identities and decisions, not copied aggregate
claims. At minimum include:

- task ID and task digest;
- corpus digest/version used for calibration;
- IDs of at least three materially different validated configurations;
- valid observation count per configuration;
- trial/run IDs or a content-addressed health/report artifact digest;
- observed solve/timeout/invalid rates;
- discrimination result and unavailable reason;
- author and empirical difficulty;
- reviewer decision, date, and rationale;
- accepted-alternative/evaluator-dispute review status.

The schema must reject unknown fields, duplicate tasks/configurations, stale
task digests, and non-current corpus identities.

**Verify**: unit tests load valid records and reject malformed, stale, and
duplicate records.

### Step 2: Separate structural release health from activation eligibility

Keep existing structural gates, but add explicit calibration gates:

- every `active` task has a current calibration record;
- at least three distinct configuration IDs are present;
- each record is derived from strictly validated studies from Plan 009;
- invalid/timeout observations are retained and summarized;
- task digest and corpus digest match the release candidate;
- reviewer decision is explicit;
- quarantined/deprecated/retired tasks do not enter active scoring.

A corpus may pass structural health while remaining `calibrating`; report these
states separately. Do not call a calibrating corpus release-eligible for active
leaderboard claims.

**Verify**: a synthetic structurally healthy corpus with no calibration must
fail the active-release gate with a precise reason.

### Step 3: Add a calibration-record generation command

Add a CLI command that reads validated current studies and emits a draft
calibration record/report without making activation decisions. It must:

- use the strict study validator;
- require exact corpus/task identities;
- deduplicate `(configuration_id, run_id, task_id)` cells;
- report unavailable discrimination honestly;
- include invalid and incomplete attempts;
- never edit lifecycle state automatically.

Choose a name consistent with existing commands, such as
`calibration-report`. Write output only to an explicitly supplied path.

**Verify**: CLI tests cover zero observations, fewer than three configurations,
duplicate cells, mismatched corpus, and a sufficient synthetic dataset.

### Step 4: Establish migration behavior for the current corpus

The current 2.0.0 corpus has no current-digest empirical observations. Choose
one honest migration:

1. mark every task/corpus `calibrating` and make active publication ineligible
   until authorized runs are completed; or
2. if qualifying current-digest studies exist outside the checked repository,
   import only their sanitized identities and reviewed calibration records.

Do not grandfather tasks as active solely because older corpus versions have
model results. Do not run paid calibration automatically.

This is a maintainer decision. If no decision was supplied, implement option 1
and document the operational follow-up, but do not publish it without review.

**Verify**: release check output clearly says structurally healthy but
calibration-incomplete, rather than a generic failure.

### Step 5: Document activation and review workflow

Update governance and authoring docs with:

- who creates draft calibration records;
- which evidence must be reviewed manually;
- how a task moves from calibrating to active;
- when changed task digests invalidate calibration;
- how quarantine and recalibration work;
- why model performance does not automatically determine difficulty/state;
- minimum evidence versus optional repetitions when budget is constrained.

Resolve the current ambiguous wording around "repeated trials when the budget
permits": state precisely which minimums are mandatory for activation.

**Verify**: release error messages and docs use the same state names and minimums.

### Step 6: Run authorized calibration later as a separate operation

Do not perform this step without explicit budget and model authorization. When
authorized, run at least three materially different configurations against the
final post-Plan-011 corpus, generate records, review them, quarantine disputed
or nondiscriminating tasks, then regenerate release evidence.

**Verify when authorized**: active release check passes with current task and
corpus digests and no missing calibration records.

## Test plan

- Lifecycle parser validates every state and rejects conflicts.
- Active task without calibration fails.
- Calibrating task is excluded from active score and reported clearly.
- Stale task/corpus digest invalidates calibration.
- Fewer than three configurations fails activation.
- Duplicate configuration/run/task evidence fails.
- Unknown/aggregate-only/legacy studies cannot satisfy current calibration.
- Invalid and incomplete attempts remain visible in calibration summaries.
- Sufficient synthetic evidence plus explicit reviewer decision passes.

## Done criteria

- [ ] Lifecycle state is explicit per task or per release-controlled task entry.
- [ ] Active release eligibility requires current calibration evidence.
- [ ] Calibration records bind corpus, task, configuration, and run identities.
- [ ] A structurally healthy but uncalibrated corpus is reported as calibrating, not active.
- [ ] No paid runs or publication occurred without authorization.
- [ ] Release/report/CLI tests pass.
- [ ] Governance defines mandatory calibration minimums unambiguously.
- [ ] Current corpus migration state is honest and reviewed.
- [ ] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- The operator wants to preserve `active` status without current-digest
  calibration evidence.
- Calibration evidence exists only in unsanitized private artifacts that cannot
  be referenced safely.
- Plan 009's strict validator or Plan 011's final corpus digest is not available.
- Implementing the gate would require automatically paying for or launching
  external model runs.
- Governance stakeholders have not decided the mandatory minimum observation
  count or whether one trial per configuration is sufficient.

## Maintenance notes

Any prompt, starter, evaluator, rubric, or contract change that changes a task
digest must invalidate that task's calibration. Structural evaluator health and
empirical calibration are separate gates; neither substitutes for the other.
Reviewers should resist automatic activation based on a numeric threshold alone—
disputes and accepted alternatives still require human review.
