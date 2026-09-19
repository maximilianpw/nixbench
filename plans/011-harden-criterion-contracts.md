# Plan 011: Make rubric criteria independently evaluable and negatively covered

> **Executor instructions**: This is a corpus-contract migration. Follow the
> plan step by step, run every verification gate, and do not change a task's
> accepted behavior without recording the release impact. If a STOP condition
> occurs, report it instead of weakening a check. Update `plans/README.md` when
> complete unless a reviewer owns the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- tasks contracts tests/evaluator_contracts.py tests/test_evaluator_contracts.py nixbench/release.py nixbench/cli.py docs/authoring.md docs/scoring.md docs/releases/2.0.0.md corpus/releases/2.0.0.json`
> Any task/evaluator/contract drift is material. Recompute the inventory in
> Step 1 before editing.

## Status

- **Priority**: P1
- **Effort**: L
- **Risk**: HIGH
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

The corpus now supports partial credit, but many evaluator expressions still
collapse malformed candidates into an all-false payload. Contract coverage also
counts a criterion as covered when it appears only in a passing fixture, and
the release checker does not verify that a fixture's named criterion has the
expected outcome. Confirmed current inventory: 68 of 117 required criteria lack
a targeted rejecting fixture; 16 of 77 rejecting fixtures emit Nix evaluation
errors; 24 rejecting fixtures lose more than one criterion. Partial scores and
failure classes must reflect candidate behavior rather than evaluator fragility.

## Current state

- `tasks/module-stale-option-migration/tests/check.sh:10-34` wraps individual
  boolean expressions with `passes`, but a missing nested attribute still
  aborts the whole generated Nix output in a confirmed fixture. The shell
  fallback at `:39` writes every criterion as false.
- `contracts/module-stale-option-migration/retains-stale-option-path/candidate/module.nix`
  preserves Plasma, graphics, and KDE Connect, yet currently scores all four
  criteria false because the SDDM access aborts evaluation.
- `tests/evaluator_contracts.py:187-201` computes criterion coverage as a union
  of labels, regardless of fixture outcome.
- `tests/test_evaluator_contracts.py:80-99` checks only the named criterion,
  while most case manifests do not declare the complete expected criterion
  vector.
- `nixbench/release.py:748-788` records manifest labels as coverage but checks
  only overall pass/fail, not the named criterion result.
- Task criteria are release-controlled benchmark contracts. Evaluator,
  contract, rubric, or accepted-solution changes require a corpus version and
  release-manifest decision under `docs/benchmark-governance.md`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Contract suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts tests.test_corpus_health -v` | all pass |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | exit 0 with system dependencies |
| Reference validation | `python3 bench.py validate --solution reference` | every reference full score |
| Starter validation | `python3 bench.py validate --solution starter` | every starter validly rejected |
| Release check | `CI=1 PYTHONDONTWRITEBYTECODE=1 python3 bench.py release-check --corpus-root . --json` | eligible after version/manifest update |
| Shell syntax | `for f in tasks/*/tests/check.sh; do sh -n "$f" || exit 1; done` | exit 0 |

## Scope

**In scope**:
- `tests/evaluator_contracts.py`
- `tests/test_evaluator_contracts.py`
- `nixbench/release.py`
- `nixbench/cli.py` where corpus-health duplicates contract execution
- `contracts/**/case.toml`
- New/updated `contracts/**/candidate/*`
- Task evaluators under `tasks/*/tests/check.sh` that fail independent scoring
- Task metadata only when a criterion definition itself is wrong
- `docs/authoring.md`
- `docs/scoring.md`
- Release note/manifest/version files required by governance

**Out of scope**:
- Broad task redesigns listed separately in the audit, such as adding a real
  `nix flake check`, parsing Nushell, or changing the Rust URL contract. Those
  can be follow-up corpus changes after the scoring foundation is reliable.
- LLM judges or subjective prose grading.
- Changing all criterion weights merely for variety.
- Recalibration execution; Plan 012 follows this migration.

## Git workflow

- Suggested branch: `advisor/011-harden-criterion-contracts`
- Use logical commits: contract schema/runner, evaluator totality repairs,
  negative fixtures, then release metadata.
- Do not publish the new corpus release or overwrite historical results.

## Steps

### Step 1: Generate and commit a criterion-boundary inventory

Add a test/helper that computes, per required criterion:

- at least one passing fixture;
- at least one rejecting fixture naming that criterion;
- fixture candidate digest, to identify duplicate candidates presented as
  independent evidence;
- complete observed criterion vector;
- whether evaluator logs contain an ordinary Nix evaluation error.

The initial test should reproduce the current counts (68 missing targeted
rejects, subject to drift) and fail under the new desired policy.

Do not commit a generated report outside tests unless it is a release artifact
specified by governance.

**Verify**: the new policy test fails and prints actionable `task/criterion`
identifiers.

### Step 2: Extend contract schema with expected criterion vectors

Add a required schema field for current contract cases, for example:

```toml
[expected_criteria]
criterion-a = true
criterion-b = false
```

The exact TOML shape may differ, but it must specify every declared criterion.
Update `EvaluatorContractCase`, manifest validation, and shared execution so:

- actual criteria exactly equal the expected vector;
- a passing fixture has all required criteria true;
- a rejecting fixture has its named criterion false;
- targeted fixtures preserve unrelated criteria true unless the case explicitly
  documents a coupled failure;
- unknown/missing criterion IDs reject the manifest.

Move contract loading/execution into one production module used by unit tests,
`corpus-health`, and `release-check`; do not keep the current reduced duplicate
implementations in `nixbench/release.py` and `nixbench/cli.py`.

**Verify**: loader tests reject incomplete vectors and release-health tests
prove named-criterion disagreement fails the gate.

### Step 3: Make evaluator criteria total

Repair evaluators that abort before independent criterion results are produced.
Use Nix patterns that keep missing attributes inside a successful top-level
result, such as guarded attrset navigation, `or` defaults at each level, or
separate `builtins.tryEval` results forced before constructing the final JSON.

Start with the 16 confirmed error-producing reject fixtures:

- `container-native-vs-oci/uses-oci-container-backend`
- `debug-network-false-lead/generic-evidence-omits-observed-facts`
- `debug-network-false-lead/network-diagnosis-never-returns-unknown`
- `fhs-binary-wrapper/fhs-wrapper-fetches-an-unpinned-empty-source`
- `fhs-binary-wrapper/system-activation-creates-fhs-paths`
- `fhs-binary-wrapper/system-timer-links-global-library`
- `flake-per-system-outputs/flake-app-missing-package-metadata`
- `home-manager-extra-special-args/home-manager-forwards-only-known-inputs`
- `issue-report-quality/issue-report-missing-expected-behavior`
- `lang-attrsets-normalize/attrset-normalizer-removes-argument-defaults`
- `module-service-options/service-uses-an-unavailable-lib-helper`
- `module-stale-option-migration/retains-stale-option-path`
- `overlay-module-boundary/overlay-exports-an-unrelated-attribute`
- `overlay-module-boundary/overlay-uses-prev-for-runtime-inputs`
- `overlay-override-package/overlay-debug-package-bypasses-final`
- `purity-wrapper-derivation/pure-wrapper-uses-forbidden-get-exe-helper`

An ordinary candidate syntax/import failure may still produce an all-false
valid rejection payload. A missing field relevant to one criterion must not
automatically erase unrelated criteria.

**Verify**: all 16 fixtures produce valid criterion payloads without evaluator
error logs, matching their declared vectors.

### Step 4: Add a targeted rejecting fixture for every required criterion

For each currently uncovered required criterion, create a minimal mutation of
a valid candidate that violates that criterion while preserving unrelated
criteria wherever semantically possible. Avoid using the starter as the sole
negative boundary because starters usually violate many requirements.

Reject duplicate candidate digests as independent criterion evidence unless
the manifests intentionally test different evaluator inputs and document why.

This step will add many fixtures. Keep each case small and name it after the
behavioral violation, not `rubric-<criterion>`.

**Verify**: the inventory reports zero required criteria without a targeted
rejecting fixture.

### Step 5: Strengthen release gates

Update corpus health and release checks to require:

- complete expected vectors;
- actual vector equality on repeated runs;
- named criterion outcome equality;
- one targeted reject per required criterion;
- at least one valid alternative passing fixture per task;
- deterministic repeated vectors;
- no known-issue skips for active tasks.

Ensure `delete` and `rename` contract operations are applied identically by the
unit suite, corpus-health command, and release checker.

**Verify**: a synthetic mislabeled fixture and a fixture whose named criterion
stays true both make release eligibility false.

### Step 6: Version and document the corpus migration

Because evaluator acceptance and partial scores change, follow governance for a
major corpus release unless the current 2.0.0 worktree has not been published.
Update:

- `corpus.toml` version;
- release note;
- checked release manifest;
- task digests and corpus digest;
- documentation for the contract schema and targeted-negative requirement.

Do not rescore historical studies or pool old/new corpus digests.

**Verify**: full release check passes by recomputing evidence, not by a stale
cached report.

## Test plan

- Contract loader rejects missing/extra expected criterion keys.
- Contract executor compares complete vectors.
- Release health applies delete/rename operations identically to unit tests.
- Missing nested attributes preserve unrelated criterion credit.
- Syntax-invalid candidates produce valid all-false rejection payloads.
- Every required criterion has a targeted negative.
- Duplicate candidate-digest detection is tested.
- Reference and starter validation remain healthy.

## Done criteria

- [ ] Zero required criteria lack a targeted rejecting fixture.
- [ ] All contract cases declare complete expected criterion vectors.
- [ ] Unit tests, corpus-health, and release-check share one contract executor.
- [ ] The 16 confirmed evaluator-error fixtures no longer emit evaluator errors.
- [ ] Unrelated criteria retain credit for isolated defects.
- [ ] Reference solutions all earn full score.
- [ ] Starters all reject with valid measurements.
- [ ] Corpus version, release note, and checked manifest honestly record the contract change.
- [ ] Full test suite and release check pass.
- [ ] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- A required criterion cannot be violated independently by any plausible
  candidate; it may need to be merged or redefined rather than covered with a
  fake fixture.
- Fixing evaluator totality changes what the public prompt requires.
- The operator has not decided whether current 2.0.0 is published/immutable.
- A task requires subjective grading to express its intended criterion.
- The fixture count becomes unmanageable without first redesigning criterion
  granularity; report the affected tasks and proposed schema change.

## Maintenance notes

A passing reference and failing starter are smoke tests, not a validated
measurement boundary. Every future criterion must ship with a targeted negative
fixture and a complete expected vector. Reviewers should scrutinize all-false
fallbacks: they are valid for whole-candidate parse failure, not for ordinary
missing fields in one rubric dimension.
