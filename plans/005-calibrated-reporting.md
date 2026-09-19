# Plan 005: Preserve task observations and publish calibrated statistics

> **Executor instructions**: Build reports from normalized valid task
> observations. Keep one canonical statistics implementation in Python; do not
> duplicate formulas in export consumers. Preserve current aggregate fields for
> compatibility and update `plans/README.md` when complete.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- nixbench/study.py nixbench/export.py nixbench/runner.py tests/test_runner.py tests/test_export.py docs/reproducibility.md docs/scoring.md site/src/data/benchmark.ts; git status --short -- nixbench tests docs site/src/data/benchmark.ts`
> This includes committed and local work. Plans 001 and 004 intentionally change
> identities and result fields. Site code is read-only/out of scope here; if it
> changed, preserve exporter compatibility rather than editing the UI.

## Status

- **Status**: DONE
- **Priority**: P2
- **Effort**: L
- **Risk**: MED
- **Depends on**: `plans/004-rubric-scoring-validity.md`
- **Category**: tech-debt
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

Study summaries currently collapse rich task results into corpus totals. That
prevents category, difficulty, task-stability, criterion-failure, and
corpus-sensitivity analysis without reopening every run directory. Existing t
intervals describe repeated whole-corpus run variation only, but the docs do not
state that limitation. This plan retains the task-by-trial matrix, produces
stratified and task-health reports with explicit denominators, and makes Python
the canonical statistics implementation.

## Current state

- `TaskRunResult` contains task ID, category, difficulty, score, pass status,
  timing, and score detail.
- `nixbench/study.py:82-110` reduces a full trial to pass count, total score,
  total time, and timeout count.
- `nixbench/study.py:49-79` computes clipped Student's t intervals over repeated
  full-corpus totals.
- `nixbench/export.py:81-145` exports trial totals and discards study estimates.
- `docs/scoring.md:41-54` names failure classes, but they are not currently
  aggregated.
- Current corpus strata are uneven: modules 9, packages 6, debugging/flakes/
  nix-language 3 each, overlays 2, and three one-task categories. Category
  results for small strata must be labeled descriptive rather than presented as
  stable category estimates.

Use one deep reporting module (`nixbench/reporting.py`) whose interface accepts
normalized observations and returns versioned report data. CLI, export, and
docs must not reimplement formulas.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Study/report tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_runner tests.test_reporting tests.test_export -v` | all pass |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |
| Example report | `python3 bench.py report-study --study-path tests/fixtures/studies/complete-v2/summary.json --json` | valid versioned JSON |

## Scope

**In scope**:

- `nixbench/study.py`
- `nixbench/export.py`
- `nixbench/reporting.py` (new)
- `nixbench/cli.py`
- result/study schema tests in `tests/test_runner.py`
- `tests/test_reporting.py` (new)
- `tests/test_export.py`
- `docs/reproducibility.md`, `docs/scoring.md`, `docs/benchmark-design.md`
- optional checked methodology fixtures under `tests/fixtures/`

**Out of scope**:

- Site components, charts, CSS, or visual presentation.
- Recomputing or rewriting historical raw run artifacts in place.
- Automatically changing author difficulty labels.
- Claiming that the fixed task corpus is a random sample of all Nix work.
- Authoring new benchmark tasks; Plan 006 owns corpus expansion.

## Git workflow

- Branch: `advisor/005-calibrated-reporting`
- Suggested commit: `feat: add task-level benchmark reporting`
- Do not push or publish generated benchmark claims without authorization.

## Steps

### Step 1: Persist the task-by-trial observation matrix

Extend `build_study_trial` so each trial contains a compact `observations` list
with, at minimum:

- task ID and task content/version identity;
- category and author difficulty;
- measurement status and task outcome;
- score, max score, normalized score;
- passed criteria and failed criteria;
- failure classes;
- agent and evaluator durations;
- agent timeout and infrastructure events.

Keep existing total fields, but derive them from observations and assert their
consistency before writing. Increment study schema version. Read Plan 004's
`attempts` ledger as a separate exclusion population: invalid/incomplete
attempts contribute to invalid-attempt rates and reasons but never to score
estimands. Add compatibility loading that can hydrate old studies from their
referenced run summaries when available; otherwise label them
`aggregate_only = true` and do not invent task observations.

**Verify**:
unit tests prove aggregate fields equal observation-derived values and invalid
measurements cannot appear in a publishable trial.

### Step 2: Define canonical statistical result objects

In `nixbench/reporting.py`, version every method result with:

- `method`
- `method_version`
- `sampling_unit`
- `n`
- included/excluded IDs and reasons
- estimate, bounds, standard deviation/range where applicable
- warnings

Implement these methods using only Python standard library unless an existing
project dependency policy explicitly changes:

1. **Fixed-corpus run variation**: retain Student's t mean interval over
   independent complete full-corpus trials. Do not clip silently; include raw
   bounds plus a separately bounded display interval if needed. Emit no interval
   for one trial and a small-sample warning below five.
2. **Per-task binary stability**: Wilson interval for pass probability across
   valid repeated trials.
3. **Criterion frequency**: raw numerator/denominator for each criterion and
   failure class; avoid unnecessary intervals for tiny samples.
4. **Task/run resampling sensitivity**: operate only on a complete rectangular
   matrix of valid observations for the same task IDs and configuration. If the
   matrix is incomplete, emit no interval and a reason; never impute. For each
   of exactly 10,000 replicates, sample trial indices with replacement, then
   sample task IDs with replacement from the stratum, and compute the macro
   normalized score over the sampled cells. Seed `random.Random` from SHA-256 of
   `corpus_id + configuration_id + stratum_id + method_version`. Use the
   standard linear-interpolated quantile definition equivalent to Hyndman–Fan
   type 7 for the 2.5th and 97.5th percentiles. Label this a
   resampling/sensitivity interval, not population generalization.

If fewer than five tasks exist in a stratum, do not produce a task-resampling
interval for that stratum.

**Verify**:
use fixed hand-calculated fixtures for t and Wilson values; use deterministic
snapshot-like numeric assertions for bootstrap output and seed stability.

### Step 3: Add transparent strata and weighting reports

Generate summaries for:

- whole corpus;
- category;
- author-assigned difficulty;
- task;
- criterion/failure class.

Every stratum must include task count, valid observation count, invalid attempt
count, trial count, mean normalized score, pass rate, and
descriptive/estimable status. Mark strata with fewer than five tasks
`descriptive_only = true`.

Define estimands exactly:

- **macro task score**: for each task, average normalized score across valid
  trials; then take the unweighted mean across tasks in the stratum;
- **macro pass rate**: for each task, average its binary pass indicator across
  valid trials; then take the unweighted mean across tasks;
- **point-weighted score**: sum earned points across all valid task-trial cells
  divided by sum available points across those same cells.

Do not pool cells first when computing macro metrics.

Do not introduce editorial category weights. Validate categories against the
vocabulary documented in `docs/task-format.md`; unknown categories fail corpus
release validation rather than silently becoming new groups. Compute duration
summaries only within one `timing_environment_id`. When a correctness
configuration spans multiple timing environments, report separate timing
strata and refuse a combined timing interval.

**Verify**:
fixtures with unequal max scores distinguish macro and point-weighted results;
one-task categories are marked descriptive.

### Step 4: Generate a corpus health artifact

Add `bench.py corpus-health --studies-dir ... --output ...` or an equivalent
command producing versioned JSON keyed by corpus digest. Include per task:

- reference full-score check;
- starter rejection;
- pass/reject fixture counts;
- criterion coverage;
- evaluator determinism result (same fixture/reference run twice);
- evaluator median/max runtime;
- observed pass and timeout rates;
- invalid-measurement rate;
- per-task Wilson interval when trials permit;
- discrimination statistic only when sample size/configuration diversity meets
  a documented threshold;
- author difficulty and empirical solve-rate band, kept as separate fields.

For discrimination, prefer an interpretable point-biserial correlation between
binary task outcome and leave-one-task-out total score. Return null with a
reason when sample size is inadequate. Never auto-relabel task difficulty.

**Verify**:
health-report tests cover adequate and inadequate sample sizes, deterministic
ordering, and missing historical observations.

### Step 5: Export canonical statistics without changing site design

Extend `export-site` or add a general `export-report` path so publication data
contains:

- corpus/configuration IDs from Plan 001;
- normalized observations or a separate linked data file;
- Python-computed estimates and method metadata;
- invalid measurement counts;
- stratum counts and descriptive-only flags;
- compatibility trial fields currently consumed by the site.

Do not edit React/Astro components. Do not maintain a second t-critical-value
table or formula in new code. If current site code recomputes estimates, export
canonical values now and leave UI migration as a separate visual/product task.

**Verify**:
export tests prove method metadata and observations survive JSON export and old
required fields remain present.

### Step 6: Rewrite methodology documentation precisely

Document that the fixed-corpus Student's t interval estimates the mean outcome
of hypothetical independent repetitions of the **same corpus under the same
configuration**, assuming approximate normality of the trial statistic. It does
not estimate:

- a single future-run prediction interval;
- uncertainty caused by evaluator correctness;
- representativeness of all Nix work;
- model identity certainty;
- a direct significance test between configurations.

Document the bootstrap as corpus-composition sensitivity, not proof of
population generalization. Require raw points, ranges, sample sizes, timeout
rates, and invalid-measurement rates beside intervals in publishable reports.

### Step 7: Run full verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: all tests and corpus checks pass. Then run:

```sh
python3 bench.py report-study \
  --study-path tests/fixtures/studies/complete-v2/summary.json \
  --json | python3 -m json.tool >/dev/null
```

Expected: exit 0.

## Test plan

- Observation-derived totals exactly match compatibility totals.
- T intervals, Wilson intervals, and bootstrap outputs use explicit methods and
  deterministic tests.
- One-trial and small-task strata receive warnings/null intervals.
- Invalid measurements are excluded with reasons and reported separately.
- Macro and point-weighted scores differ correctly on unequal task weights.
- Category/difficulty/task reports preserve transparent denominators.
- Historical aggregate-only studies are never presented as task-level data.
- Exports contain canonical statistics and preserve old nonvisual fields.

## Done criteria

- [x] New study summaries retain normalized task observations.
- [x] Python is the sole canonical statistics implementation for new reports.
- [x] Reports include whole-corpus, category, difficulty, task, criterion, and
  failure-class views with explicit denominators.
- [x] Small strata are marked descriptive only.
- [x] Corpus-health JSON can be generated deterministically.
- [x] Documentation precisely scopes every uncertainty measure.
- [x] Existing site data consumers can continue reading compatibility fields.
- [x] Full verification passes.
- [x] No site UI files changed.
- [x] `plans/README.md` marks Plan 005 DONE.

## STOP conditions

- Implementing task-level analysis would require fabricating observations for
  historical aggregate-only studies.
- A proposed interval is described as generalization beyond the fixed corpus
  without a defined task sampling frame.
- Statistics need a new heavy dependency solely for convenience; report the
  tradeoff before adding it.
- Export compatibility would require silently changing existing field meaning.

## Maintenance notes

Method names and versions are part of result provenance. Any formula or
inclusion-rule change requires a method-version bump. Difficulty calibration is
a review input, not an automated label rewrite. Reviewers should scrutinize
denominators and exclusion reasons before numerical output.
