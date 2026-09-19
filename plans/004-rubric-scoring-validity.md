# Plan 004: Introduce rubric-based partial scoring and measurement validity

> **Executor instructions**: This is a benchmark-schema migration. Implement
> compatibility reads, but make new publishable corpus releases use structured
> criteria. Do not assign points from free-form notes. Run all verification
> gates and update `plans/README.md` when complete.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- nixbench/runner.py nixbench/task.py nixbench/study.py nixbench/cli.py tasks contracts tests docs/scoring.md docs/task-format.md corpus.toml corpus protocols; git status --short -- nixbench tasks contracts tests docs corpus.toml corpus protocols`
> This includes committed and local work. Plans 001–003 intentionally change
> identities, fixtures, and evaluators. If runner result or score-file schemas
> changed independently, stop and reconcile.

## Status

- **Status**: DONE
- **Priority**: P1
- **Effort**: L
- **Risk**: HIGH
- **Depends on**: `plans/003-repair-evaluator-validity.md`
- **Category**: tech-debt
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

The harness supports evaluator-provided scalar scores, but none of the bundled
evaluators currently uses them. A narrow failed assertion therefore produces
the same zero as a completely broken solution. Scalar evaluator totals are also
not auditable against a declared rubric. Separately, evaluator timeouts, exit
codes `2+`, and malformed score files can be counted as model failures. The fix
is a declared criterion rubric whose totals and failure classes are computed by
the harness, plus an explicit measurement-validity state separate from task
outcome.

## Current state

- `nixbench/task.py:19-28` requires only task-level `max_score`.
- `nixbench/runner.py:144-152` treats all non-passing evaluator outcomes as
  failed tasks, then defaults missing scores to zero.
- `nixbench/runner.py:315-379` accepts a JSON number or object with a numeric
  `score`, but does not validate criterion meaning.
- `docs/task-format.md:60-64` reserves evaluator exit `1` for candidate
  rejection and `2+` for evaluator infrastructure errors, but the runner does
  not preserve that distinction in study outcomes.
- `docs/scoring.md:30-37` recommends a 70/15/10/5 rubric, but it is prose only.
- All 29 tasks currently have `max_score = 100`; no evaluator writes
  `$NIXBENCH_SCORE_FILE`.

## Target interface

Task metadata declares stable criteria. Evaluators report criterion status. The
harness computes score, failure classes, pass consistency, and measurement
validity.

Example metadata:

```toml
max_score = 100

[[criteria]]
id = "evaluates"
points = 25
required = true
failure_class = "evaluation"

[[criteria]]
id = "preserves-runtime-inputs"
points = 20
required = true
failure_class = "wrong-value"
```

Example evaluator score payload:

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

Evaluators must not submit point totals or arbitrary failure classes in schema
2. The harness derives both from metadata.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Runner tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_runner tests.test_task_loading -v` | all pass |
| Contract tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts tests.test_corpus_health -v` | all pass |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |
| Corpus checks | `python3 bench.py validate --solution reference && python3 bench.py validate --solution starter` | expected outcomes |

## Scope

**In scope**:

- `nixbench/task.py`
- `nixbench/runner.py`
- `nixbench/study.py`
- `nixbench/cli.py`
- `nixbench/agent_status.py` (new trusted completion-attestation parser)
- optional new `nixbench/scoring.py` as the single scoring module
- all `tasks/*/metadata.toml`
- all `tasks/*/tests/check.sh`
- relevant evaluator contract fixtures and tests
- `tests/test_runner.py`, `tests/test_task_loading.py`,
  `tests/test_corpus_health.py`, `tests/test_cli.py`
- `docs/scoring.md`, `docs/task-format.md`, `docs/authoring.md`,
  `docs/reproducibility.md`
- corpus version/release artifacts from Plan 001

**Out of scope**:

- LLM-judged or subjective style scores.
- Changing task semantics fixed in Plan 003.
- Statistical analysis beyond storing valid observations; Plan 005 owns it.
- Site UI work.
- Retroactive score conversion of old artifacts.

## Git workflow

- Branch: `advisor/004-rubric-scoring-validity`
- Use separate commits for schema/harness and task rubric migration.
- Do not publish new results or push without authorization.

## Steps

### Step 1: Model and validate criteria in task metadata

Add immutable rubric types in `nixbench/scoring.py` or `task.py`. Validation
must require for schema-2 tasks:

- criterion IDs are lowercase slugs and unique;
- points are positive finite numbers;
- points sum exactly to `max_score` without floating ambiguity (prefer integers
  for this corpus);
- `required` is boolean;
- `failure_class` belongs to a controlled vocabulary;
- at least one required functional criterion exists;
- every criterion that maps to a public prompt requirement has
  `required = true`;
- `required = false` is allowed only for an objective supplemental quality
  check whose failure does not contradict the prompt.

Start with these failure classes unless a task requires another objectively
defined class:

- `syntax`
- `evaluation`
- `missing-attr`
- `wrong-value`
- `unavailable-helper`
- `impurity`
- `overfit`
- `maintainability`
- `formatting`

Do not use failure classes for infrastructure events; those belong to
measurement status.

Maintain read support for legacy tasks without criteria, clearly marked
`scoring_schema = "legacy-binary"` in result data. Require structured criteria
for a publishable current corpus.

**Verify**:
unit tests reject duplicate IDs, unknown classes, point-sum mismatch,
non-finite values, and malformed booleans.

### Step 2: Parse criterion outcomes and compute score centrally

Replace the score reader's authoritative scalar path with a scoring module that:

1. validates score-file safety exactly as today;
2. recognizes schema 2 objects;
3. requires exactly the declared criterion IDs (no missing or unknown IDs);
4. requires boolean outcomes;
5. computes score as the sum of points for true criteria;
6. derives failed criterion IDs and unique failure classes;
7. retains bounded, JSON-safe notes only as diagnostics.

Keep legacy JSON number and `{ "score": ... }` reads for historical artifacts
and explicitly mark them legacy. A new task with metadata criteria must reject a
legacy scalar score as an invalid measurement.

Evaluator exit consistency:

- exit `0` requires every `required = true` criterion to be true;
- exit `1` means candidate rejection and may still earn partial credit;
- disagreement between exit status and required criteria is an invalid
  measurement, not a model failure.

**Verify**:
runner tests cover full, partial, zero, unknown/missing criteria, legacy reads,
exit/criterion disagreement, and malformed payloads.

### Step 3: Separate measurement status from task outcome

Extend `TaskRunResult` with explicit fields while preserving `passed`:

- `measurement_status`: `valid`, `invalid`, or `incomplete`;
- `task_outcome`: `pass`, `fail`, or `agent-timeout` when valid;
- `invalid_reason`: controlled value or null;
- `scoring_schema`;
- `criteria`: normalized criterion observations;
- `failure_classes`: derived semantic classes;
- `infrastructure_events`: e.g. evaluator timeout, evaluator error,
  agent-process-error, invalid-score-payload.

Classification rules:

- for `solution_mode=agent` with no timeout: evaluator exit `0`/`1`, no
  evaluator timeout, valid criteria payload, successful launcher preflight, and
  valid required agent-completion attestation → valid;
- agent timeout is attested by the harness's own timeout/process-group event,
  not by a completion record from the killed launcher. With successful launcher
  preflight and a valid evaluator result it is a valid `agent-timeout` outcome;
- `solution_mode=reference` and `starter` do not run an agent and therefore do
  not require agent completion attestation;
- evaluator timeout, evaluator exit `2+`, invalid/missing required score payload,
  exit/criteria disagreement, failed/missing required completion attestation,
  or harness exception → invalid measurement;
- non-timeout agent process error → invalid measurement;
- `incomplete` is reserved for an interrupted study attempt that did not run the
  full selected task set. It has no score denominator and is never publishable.

Add a trusted completion-attestation channel to prevent the documented case
where model transport failed but the wrapper exited zero. `run_task` creates a
status-file path outside the editable worktree and passes it only to the
configured launcher adapter as `NIXBENCH_AGENT_STATUS_FILE`. A publishable
protocol from Plan 001 must declare `completion_attestation = "required"`.
The trusted launcher—not the model prompt—atomically writes JSON containing
schema version, successful preflight evidence, `completed`, provider/transport
error state, and actual launcher exit. Each publishable adapter must derive
`completed` and transport state from authoritative native machine-readable
provider/harness events, not log keyword matching. An adapter that cannot do so
is nonpublishable. Missing, malformed, contradictory, or transport-error status
makes a non-timeout agent measurement invalid even if the shell exit code is
zero. Generic commands
without a launcher adapter remain usable for local development but are marked
unattested and nonpublishable.

Do not count invalid or incomplete measurements in benchmark score
denominators. Preserve every attempted trial in a study-level `attempts` ledger
with observations and exclusion reasons. Only complete all-valid attempts enter
`trials`, `trial_count`, and estimates. `passed` remains true only for valid
`task_outcome=pass`.

**Verify**:
unit tests exercise every rule and prove evaluator infrastructure errors no
longer become zero-score model failures.

### Step 4: Design objective rubrics for all 29 tasks

For each task, add 4–8 binary criteria. Use requirement-level points, not
subjective percentages. Guidance:

- approximately 60–75 points for core functional/evaluation behavior;
- 15–30 for preservation, alternate hidden inputs, or purity constraints;
- at most 10–15 for objectively checkable maintainability/formatting;
- do not add style criteria when the evaluator cannot distinguish them without
  taste judgments.

Every public prompt requirement should map to at least one criterion. Every
criterion should map to a public requirement or a generic integrity invariant
such as parsing/evaluation. Include a stable criterion ID in contract fixture
metadata so test cases identify which requirement they exercise.

Do not force every task into 70/15/10/5. That recommendation is a ceiling and
shape, not a substitute for task-specific binary checks.

**Verify**:
a corpus-health test checks criterion uniqueness, exact point totals, prompt
mapping, and at least one fixture associated with every required criterion.

### Step 5: Refactor each evaluator to report all criterion outcomes

An early parse/evaluation failure must still write a valid criterion payload
before exiting `1`. Use shell helpers local to each evaluator or a small shared
repository helper only if it does not complicate external/private corpus use.
Avoid a shallow abstraction that merely echoes JSON while every caller still
implements validation differently.

Evaluator pattern:

1. initialize every criterion false;
2. run independent checks where possible;
3. set passed criteria true;
4. atomically write schema-2 JSON to `$NIXBENCH_SCORE_FILE`;
5. exit `0` only when all required criteria pass, otherwise `1`;
6. reserve `2+` for evaluator implementation/infrastructure failure.

For assertion-heavy Nix evaluators, consider several small Nix evaluations or a
single returned attrset of criterion booleans instead of one chain that aborts
at the first failure. Keep runtime bounded by task timeout.

**Verify after each task**:
- reference: full score and pass;
- starter: less than full and reject;
- each contract fixture: expected pass/reject and expected affected criterion;
- malformed candidates produce valid zero/partial criterion payloads rather
  than infrastructure errors.

### Step 6: Update validation and study gates

`validate --solution reference` must require:

- valid measurement;
- pass outcome;
- every criterion true;
- full score.

`validate --solution starter` must require:

- valid measurement;
- fail outcome;
- less than full score.

Study recording must exclude any attempt containing invalid or incomplete
measurements from the publishable `trials` list while retaining it in the
`attempts` ledger with exact exclusion reasons. It may record agent timeouts as
valid outcomes, with counts and partial scores. Non-timeout agent/process or
attestation failures must be checkpointed to `attempts` before the CLI stops.
Publication/export must reject legacy scoring for the current corpus unless an
explicit legacy flag is supplied.

**Verify**:
focused CLI and study tests prove invalid evaluator outcomes cannot enter a
study summary.

### Step 7: Document and version the scoring contract

Update docs with:

- authoritative metadata criteria and payload schema;
- pass versus score semantics;
- valid agent timeout versus invalid infrastructure outcome;
- controlled failure classes;
- prohibition on deriving points from notes or prose similarity;
- historical scalar-score compatibility policy.

Finalize the version sequence reserved by Plan 001: Plan 003 must leave the
repaired corpus at `2.0.0-dev`; after all 29 rubric migrations pass, this plan
changes it to final `2.0.0` and records the resulting digest. If any 2.0.0 trial
was already recorded contrary to the plan order, STOP and use `3.0.0` instead.
State that historical binary scores are not converted and must not be pooled
with rubric-scored runs.

### Step 8: Run complete verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: all tests pass; references are 29/29 full score; starters are 29/29
valid rejections with explicit criterion outcomes; no evaluator emits legacy
scalar scores.

## Test plan

- Metadata rubric validation and exact point totals.
- Safe score-file handling remains fail-closed.
- Harness, not evaluator, computes points and failure classes.
- Valid partial credit on candidate failure and agent timeout.
- Invalid evaluator, harness, process, transport, or attestation outcomes never
  lower a model score and remain visible in the attempts ledger.
- A synthetic trusted launcher that emits native-style `completed=false` plus a
  transport error and exits zero is classified invalid.
- Reference/starter runs need no attestation; harness timeouts use harness-owned
  timeout evidence plus successful launcher preflight.
- Exit status and required criteria cannot disagree.
- Every task's reference/starter/fixtures exercise criterion output.
- Legacy artifacts remain readable but are excluded from new publication by
  default.

## Done criteria

- [x] All 29 tasks declare objective criteria summing to `max_score`.
- [x] All 29 evaluators emit schema-2 criterion results.
- [x] No bundled evaluator submits an authoritative scalar score.
- [x] Results distinguish measurement validity from task outcome.
- [x] Invalid evaluator/harness/transport outcomes cannot enter study estimates
  and are retained in the attempts ledger.
- [x] Contract fixtures identify the criterion they exercise.
- [x] Corpus/scoring version changed; historical artifacts remain untouched.
- [x] Full verification passes.
- [x] No site UI files changed.
- [x] `plans/README.md` marks Plan 004 DONE.

## STOP conditions

- A criterion requires subjective taste or an LLM judge to score.
- An evaluator cannot recover criterion outcomes after parse failure without
  treating an ordinary candidate error as infrastructure failure.
- Partial scoring requires changing a task's public semantic contract rather
  than decomposing existing requirements.
- Compatibility code would pool legacy and schema-2 results under one corpus or
  configuration identity.

## Maintenance notes

Criterion IDs become durable analytical keys. Rename them only with a new
scoring/corpus version. Review point allocation as benchmark methodology, not
implementation detail. Notes are diagnostic; only declared boolean criteria may
change score.
