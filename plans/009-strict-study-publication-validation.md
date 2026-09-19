# Plan 009: Strictly validate and recompute study publication identity

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update this plan's row in
> `plans/README.md` unless a reviewer told you they maintain the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- nixbench/protocol.py nixbench/study.py nixbench/reporting.py nixbench/release.py tests/test_protocol.py tests/test_runner.py tests/test_reporting.py tests/test_release.py docs/scoring.md docs/reproducibility.md`
> If in-scope files changed, compare the excerpts below with live code and stop
> on a semantic mismatch.

## Status

- **State**: DONE
- **Priority**: P1
- **Effort**: L
- **Risk**: MED
- **Depends on**: `plans/008-bind-isolation-adapter-bundle.md`
- **Category**: bug
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

The formal publication checker currently trusts several self-asserted fields in
study JSON. It does not recompute configuration identity, compare public task
IDs/digests with the release manifest, or derive normalized scores and trial
totals from primitive observations. A modified or hand-built summary can pass
publication with the wrong task matrix or impossible scores. Publication needs
one strict validator that derives all redundant fields and rejects disagreement.

## Current state

- `nixbench/protocol.py:186-199` computes configuration identity from controlled
  protocol data, but publication receives only flattened metadata and does not
  reconstruct the hash input.
- `nixbench/release.py:411-424` checks only that identity fields are truthy:

  ```python
  identity_fields = (
      "configuration_id", "protocol_id", "protocol_schema_version",
      "wrapper_prompt_sha256", "agent_command_sha256", "agent_adapter",
      "agent_adapter_sha256", "attestation_trust",
  )
  if any(not metadata.get(field) for field in identity_fields):
      reasons.append("publication configuration identity is incomplete")
  ```

- `nixbench/release.py:438-477` validates task count and same-set agreement
  between trials, but does not compare public observation task IDs or task
  digests with the release manifest.
- `nixbench/reporting.py:485` accepts finite `normalized_score`; downstream
  reporting at approximately `:833` uses it directly without proving it equals
  `score / max_score` or lies in `[0, 1]`.
- `nixbench/study.py` is the writer-side source for current schema-3 studies.
  Its normalization and aggregate derivation should become the exemplar, not a
  second competing implementation.
- Existing code represents invalid measurements explicitly. Preserve that
  vocabulary: `measurement_status`, `task_outcome`, `invalid_reason`, and
  `infrastructure_events`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Focused tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_protocol tests.test_runner tests.test_reporting tests.test_release -v` | all pass with Bubblewrap available |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | exit 0 with required system tools |
| Compile | `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py` | exit 0 |
| Release check | `CI=1 PYTHONDONTWRITEBYTECODE=1 python3 bench.py release-check --corpus-root . --json` | eligible after any required manifest update |

## Scope

**In scope**:
- `nixbench/protocol.py`
- `nixbench/study.py`
- `nixbench/reporting.py`
- `nixbench/release.py`
- A new narrowly named validation module such as `nixbench/study_validation.py`
- `tests/test_protocol.py`
- `tests/test_runner.py`
- `tests/test_reporting.py`
- `tests/test_release.py`
- `docs/scoring.md`
- `docs/reproducibility.md`

**Out of scope**:
- Site export integration; Plan 010 consumes the validator.
- Calibration policy; Plan 012 consumes validated current-corpus studies.
- Statistical-method changes. This plan validates inputs to existing methods.
- Guessing model identity from network/provider APIs.
- Retrofitting unverifiable historical aggregate-only summaries into current
  publication eligibility.

## Git workflow

- Suggested branch: `advisor/009-strict-study-publication-validation`
- Suggested commit: `fix: validate publication studies from primitive evidence`
- Do not push, publish, or rewrite historical result files without authorization.

## Steps

### Step 1: Define a canonical current-study validator

Create one production validator for current schema-3 study summaries. It must
return a normalized validated structure or raise/return structured validation
errors. Do not duplicate separate validation logic across reporting and release.

For every task observation, validate and derive:

- nonempty `task_id` and expected `task_digest`;
- controlled category and difficulty;
- finite numeric `score` and positive finite `max_score`;
- `0 <= score <= max_score`;
- `normalized_score == score / max_score` within exact or explicitly documented
  floating-point tolerance;
- criteria booleans and scoring schema consistency;
- `passed`, `measurement_status`, `task_outcome`, timeout state, and failure
  classes agree with the primitive fields;
- no duplicate `(run_id, task_id)` cells.

For every trial, derive and compare task count, score, maximum score, pass/fail
counts, measurement status, scoring schema, and task set. Do not trust stored
aggregates when they disagree.

**Verify**: add unit tests for out-of-range scores, `normalized_score = 99`,
duplicate cells, pass/criteria disagreement, and aggregate disagreement. Each
must be rejected with a stable reason.

### Step 2: Preserve the complete controlled protocol hash input

A configuration ID cannot be recomputed from hashes and selected flattened
fields unless every field used by `resolve_protocol` is retained. Add a
versioned `controlled_protocol` object or an equivalent canonical identity
payload to current study metadata. It must contain the exact non-secret values
hashed by `resolve_protocol`, including the adapter bundle identity from Plan
008.

Do not store the raw agent command or wrapper prompt; their SHA-256 values are
already the intended identity inputs. Recompute `configuration_id` using the
same shared function used by `resolve_protocol`.

Tests must prove that changing any controlled field while retaining the old ID
causes rejection.

**Verify**: protocol and study tests pass; no duplicated hash algorithm exists.

### Step 3: Compare studies against the checked release manifest

Strengthen `check_publication` so a public release requires exact equality of:

- corpus ID, version, digest, and visibility;
- observation task-ID set and manifest `active_tasks`;
- each observation `task_digest` and manifest `task_digests`;
- task count derived from the manifest;
- protocol schema and recomputed configuration identity.

For private-heldout releases, compare the hash of each observation task digest
against the manifest's opaque active-task hashes without exposing task IDs in
public output. If current private summaries intentionally omit raw task digests,
STOP and request a schema decision rather than inventing an unverifiable check.

Validate the release-manifest schema before trusting any manifest fields.

**Verify**: add a regression where a one-task public manifest names task A but
the study contains task B; publication must reject it.

### Step 4: Use the validator in reporting and publication

Call the same validator from:

- `load_study_summary`/current reporting entry points;
- `build_study_report` or its immediate boundary;
- `check_publication`.

Historical summaries must remain on an explicit legacy/aggregate-only path.
They must never become current publishable studies by filling defaults or
inventing task observations.

**Verify**: focused reporting and release tests pass, including existing
historical compatibility fixtures.

### Step 5: Document the trust boundary

Update `docs/scoring.md` and `docs/reproducibility.md` to state which values are
primitive evidence and which are recomputed redundant fields. Document that
current publication rejects altered redundant totals, task digests, protocol
identity, and normalized scores.

**Verify**: grep documentation for `configuration_id`, `task_digest`, and
`normalized_score`; each should describe derivation rather than self-assertion.

## Test plan

Add negative tests for:

- wrong task ID with correct task count;
- wrong task digest;
- duplicate task cell;
- impossible normalized score;
- score above max or negative score;
- pass state inconsistent with required criteria;
- trial totals inconsistent with observations;
- configuration ID inconsistent with controlled protocol;
- malformed release manifest;
- current summary missing the canonical protocol payload.

Add positive tests using writer-produced studies from `nixbench.study`, not
hand-built underspecified dictionaries. Keep separate explicit fixtures for
legacy aggregate-only behavior.

## Done criteria

- [x] One shared validator governs current study loading, reporting, and publication.
- [x] Configuration IDs are recomputed from retained controlled protocol data.
- [x] Public task IDs and digests exactly match the checked release manifest.
- [x] Scores, normalized scores, pass state, criteria, and trial totals are derived and cross-checked.
- [x] Duplicate cells and mismatched task matrices are rejected.
- [x] Historical summaries remain explicit legacy/aggregate-only inputs and cannot publish as current.
- [x] Focused and full test suites pass with required system tools.
- [x] Release check passes with current evidence and an appropriately versioned manifest.
- [x] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- Current study files do not retain enough non-secret protocol data to
  recompute configuration identity and adding it requires a schema/version
  decision not authorized by the operator.
- Private-heldout summaries cannot be matched to opaque manifest tasks without
  exposing task identity.
- Existing published schema-3 studies fail validation and no explicit legacy
  policy exists for them.
- The change begins altering statistical estimands rather than only validating
  their inputs.

## Maintenance notes

All future consumers—CLI reports, website export, publication bundles, and
calibration—must enter through this validator. Reviewers should reject new code
that reads `normalized_score`, aggregate totals, or `configuration_id` from raw
JSON without validating or recomputing them first.
