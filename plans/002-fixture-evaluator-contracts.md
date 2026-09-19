# Plan 002: Replace mutation-only evaluator tests with fixture contracts

> **Executor instructions**: Execute each step and verification gate in order.
> This plan must not change evaluator behavior; it builds the characterization
> seam needed by Plan 003. Stop rather than “fixing” an evaluator while moving
> tests.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- tests/test_evaluator_contracts.py tests/test_corpus_health.py contracts tasks docs/authoring.md docs/task-format.md; git status --short -- tests contracts tasks docs/authoring.md docs/task-format.md`
> This includes committed and local work. Expected drift from Plan 001 is
> limited to identity-related files. Any change to evaluator contract tests or
> task files is a STOP condition until reconciled.

## Status

- **Status**: DONE
- **Priority**: P1
- **Effort**: L
- **Risk**: LOW
- **Depends on**: `plans/001-content-addressed-identities.md`
- **Category**: tests
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

The current contract suite copies each reference solution and performs exact
text replacement. This couples tests to reference formatting and does not prove
that an independently written valid solution is accepted. Coverage is also
incomplete: four tasks have neither class of case, seven lack an invalid case,
and thirteen lack a valid alternative. A fixture-based interface gives every
evaluator an explicit two-sided contract and makes missing coverage fail CI.

## Current state

- `tests/test_evaluator_contracts.py:24-443` declares 46 invalid mutations.
- `tests/test_evaluator_contracts.py:445-692` declares 25 valid alternatives.
- `tests/test_evaluator_contracts.py:713-726` copies `reference/` over
  `starter/`, then applies exact string replacements.
- `docs/authoring.md:20-28` already requires plausible invalid candidates and
  semantically valid alternatives, but CI does not enforce this per task.
- Coverage gaps at commit `e2716e6`:
  - neither: `container-native-vs-oci`, `debug-infinite-recursion`,
    `module-path-composition`, `module-system-boundaries`;
  - no invalid: `flake-input-package-selection`,
    `home-manager-wsl-module-import`, `module-stale-option-migration`;
  - no valid: `fetcher-source-pin`, `flake-per-system-outputs`,
    `home-manager-extra-special-args`, `home-manager-xdg-files`,
    `lang-attrsets-normalize`, `overlay-module-boundary`,
    `overlay-override-package`, `package-name-lookup-contract`,
    `python-cuda-uv2nix-patch`.

The fixture runner should be a deep test module: case discovery and execution
behind one small interface. Tests should not know how overlays are copied or
how task results are interpreted.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Contract tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts -v` | all cases pass |
| Corpus tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_corpus_health -v` | all pass |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |

## Scope

**In scope**:

- `tests/evaluator_contracts.py` (new helper module)
- `tests/test_evaluator_contracts.py` (replace registry/mutation implementation)
- `contracts/<task-id>/<case-id>/case.toml` (new)
- candidate overlays under those case directories
- `docs/authoring.md`
- `docs/task-format.md`
- `.github/workflows/tests.yml` only if a dedicated contract-test command is useful

**Out of scope**:

- `tasks/*/tests/check.sh`, prompts, starters, references, or metadata.
- Changing which current candidate passes or fails.
- Partial-credit rubric fixtures; Plan 004 adds those after scoring exists.
- Site files.

## Git workflow

- Branch: `advisor/002-fixture-evaluator-contracts`
- Suggested commit: `test: add fixture-based evaluator contracts`
- Do not push without authorization.

## Steps

### Step 1: Define the fixture format and loader

Create corpus-owned cases at:

```text
contracts/<task-id>/<case-id>/
  case.toml
  candidate/...
```

`case.toml` must contain:

```toml
schema_version = 1
task_id = "package-stdenv-cli"
outcome = "pass" # or "reject"
requirement = "runtime-install"
description = "Uses cp instead of install to place the executable"
```

Optional fields may include `expected_score` later, but do not implement
partial-scoring assertions in this plan. Support `delete = ["relative/path"]`
and `[[rename]] from = "old"; to = "new"` operations, validated to stay inside
the candidate workspace, so fixtures can remove or rename obsolete starter
files. The `candidate/` directory is then overlaid on the task starter, never on
the reference. Every passing fixture must contain an independently
understandable implementation rather than a mutation script.

The fixture loader must accept an explicit `contracts_root`. Default it to the
public repository's `contracts/`, but allow an external corpus to keep its own
`contracts/` beside `corpus.toml` and `tasks/`. Do not hard-code public-repo
paths into case discovery.

Implement loader validation for slug IDs, known outcomes, nonempty requirement
and description, matching directory/task IDs, and path containment.

**Verify**:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts.ContractCaseLoadingTests -v`
→ malformed and escaping fixtures are rejected.

### Step 2: Implement one case execution seam

Create a helper such as:

```python
def run_contract_case(case: EvaluatorContractCase, *, repo_root: Path) -> tuple[TaskRunResult, str]: ...
```

It must:

1. copy the complete task into a temporary root;
2. overlay `candidate/` onto the copied task's `starter/`;
3. load the copied task with the production loader;
4. execute it through `run_task(..., solution_mode="starter")`;
5. return the result and evaluator log.

A passing case requires `result.passed`. A rejecting case requires a valid
measurement, evaluator exit `1`, no evaluator timeout, and not-passed. Until
Plan 004 introduces explicit validity, preserve current checks.

**Verify**:
run one migrated passing and one migrated rejecting case through the helper.

### Step 3: Migrate all existing mutation cases without changing behavior

For each current registry entry, create a fixture that produces the same final
candidate. Generate the initial files mechanically if useful, but commit the
resulting candidate files—not generation scripts or fragile replacement
instructions.

Before deleting the old registry, run old and new implementations against all
cases and assert identical pass/reject outcomes. Then remove the replacement
engine and dataclasses from `tests/test_evaluator_contracts.py`.

**Verify**:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts -v`
→ all migrated cases match their prior expected outcomes.

### Step 4: Add independent cases to close every coverage gap

Add at least one passing and one rejecting fixture for every task. Start with
the exact gap list in “Current state.” Requirements:

- Passing cases must differ structurally from the reference where the public
  contract allows it: reordered lists, alternate attrset composition, function
  versus attrset module forms, equivalent shell quoting, or equivalent builder
  attributes.
- Rejecting cases must violate one named public requirement while remaining
  plausible; do not use syntax garbage as the only negative test.
- For the six known false-negative candidates, add passing fixtures that are
  expected to fail under current behavior and mark them in `case.toml` with
  `known_issue = "plan-003"`. The test runner should skip only these explicitly
  marked cases with a clear reason. Plan 003 will remove all such skips.

Known regression fixtures to capture:

1. top-level NixOS module shorthand for `container-native-vs-oci`;
2. the published observation shape and a non-keyword paraphrase for
   `debug-network-false-lead` after Plan 003 updates the prompt;
3. multiline `NIX_CONFIG` for `devshell-tooling-contract`;
4. quoted Bash package path for `purity-wrapper-derivation`;
5. Python `dependencies` for `package-python-application`;
6. `lib.getLib onnxruntime` for `rust-no-network-build`.

At this stage items 2 and any fixture impossible under the current public prompt
may be represented but skipped with the named issue. Do not change prompts here.

**Verify**:
`python3 -m unittest tests.test_evaluator_contracts -v`
→ all non-known-issue fixtures pass; output lists the six intentional skips.

### Step 5: Add a completeness gate

Add a meta-test that loads every task from `tasks/` and requires:

- at least one `pass` fixture;
- at least one `reject` fixture;
- distinct case IDs;
- every fixture requirement maps to a requirement identifier declared in the
  task's contract documentation or, until Plan 004 adds metadata criteria, a
  nonempty stable string.

The gate must fail when a new task is added without fixtures.

**Verify**:
Temporarily remove one case in a temporary copied fixture tree inside a unit
test; assert the checker reports the exact missing task/outcome.

### Step 6: Document task-author expectations

Update authoring docs to require independent candidates rather than
reference-string mutations. Explain that hidden inputs are encouraged, hidden
interface assumptions are not. Require all implementation constraints to be
public or broadly normalized by the evaluator.

**Verify**:
`grep -R "exact text replacement\|string replacement" -n docs tests | cat`
→ no guidance recommends mutation-only testing.

### Step 7: Run full verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: all tests pass except the six explicitly named known-issue fixture
skips; all references pass and starters fail exactly as before.

## Test plan

- Loader rejects malformed TOML, unknown tasks, duplicate IDs, and path escapes.
- Runner overlays candidates onto starters, not references.
- Migrated fixtures preserve all prior outcomes.
- Every task has pass and reject coverage.
- Known evaluator defects are explicit skipped passing fixtures, never silent
  omissions.
- Adding a task without cases fails the completeness test.

## Done criteria

- [x] No contract case depends on exact replacement text in the reference.
- [x] All 29 tasks have at least one passing and one rejecting fixture.
- [x] The six known false negatives exist as explicit passing regressions and
  are the only allowed known-issue skips.
- [x] Existing evaluator behavior is otherwise unchanged.
- [x] Full verification passes.
- [x] No task or site files changed.
- [x] `plans/README.md` marks Plan 002 DONE.

## STOP conditions

- A migrated fixture changes outcome compared with the old registry.
- Closing a gap requires deciding whether an undocumented implementation is
  valid. Record it as a Plan 003 question instead of modifying the evaluator.
- More than the six enumerated known-issue passing fixtures require skips.
- A fixture would need hidden evaluator paths or reference files inside the
  candidate workspace.

## Maintenance notes

Passing fixtures are the primary defense against evaluator overconstraint.
Review them as carefully as references. Future task PRs should include contract
fixtures in the same commit; the completeness gate should make omission
impossible.
