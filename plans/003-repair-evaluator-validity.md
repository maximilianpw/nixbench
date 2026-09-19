# Plan 003: Repair evaluator construct validity across the corpus

> **Executor instructions**: Make every change test-first using the fixture
> suite from Plan 002. A repair must cause a named valid fixture to pass or a
> named invalid fixture to fail. Do not broadly weaken evaluators to make model
> outputs pass. Update `plans/README.md` when complete.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- tasks contracts tests/test_evaluator_contracts.py docs/benchmark-design.md docs/authoring.md; git status --short -- tasks contracts tests docs/benchmark-design.md docs/authoring.md`
> This includes committed and local work. Expected drift from Plan 002 is the
> fixture migration. If task evaluators or prompts changed for another reason,
> reconcile every affected semantic contract before proceeding.

## Status

- **Status**: DONE
- **Priority**: P1
- **Effort**: L
- **Risk**: MED
- **Depends on**: `plans/002-fixture-evaluator-contracts.md`
- **Category**: bug
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

At least six published failures are documented as evaluator-representation
mismatches rather than established Nix failures. A full evaluator review found
eleven additional semantic-boundary defects. Together they can create false
negatives, and one creates a direct false-positive hole. This plan aligns each
evaluator with its public task contract and locks the accepted boundary with
independent passing and rejecting fixtures.

## Current state

Known published caveats are documented in
`docs/runs/2026-09-10-astra-pi-isolated.md:98-105`:

- `container-native-vs-oci` assumes explicit `module.config`;
- `debug-network-false-lead` hides its observation schema and grades wording;
- `devshell-tooling-contract` requires one-line `NIX_CONFIG` syntax;
- `purity-wrapper-derivation` rejects valid shell quoting;
- `package-python-application` recognizes only `propagatedBuildInputs`;
- `rust-no-network-build` provides an unrealistically narrow fake `lib`.

Additional confirmed contract risks affect:

- `fhs-binary-wrapper`
- `home-manager-xdg-files`
- `issue-report-quality`
- `module-service-options`
- `module-stale-option-migration`
- `module-system-boundaries`
- `mutable-config-home-manager`
- `overlay-module-boundary`
- `python-cuda-uv2nix-patch`
- `string-escaping-systemd`
- `xdg-portal-merge`

No repair is currently justified for the other twelve evaluators. Do not edit
them unless a new failing contract fixture demonstrates a concrete defect.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| One task | `python3 -m unittest tests.test_evaluator_contracts -v` | named fixtures pass |
| Corpus contracts | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_evaluator_contracts tests.test_corpus_health -v` | all pass, zero skips |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |
| References | `python3 bench.py validate --solution reference` | 29/29 full score |
| Starters | `python3 bench.py validate --solution starter` | 29/29 rejected |

## Scope

**In scope**:

- the 17 task directories named above, limited to `prompt.md`,
  `tests/check.sh`, and reference changes only when the public contract itself
  must be clarified;
- their fixture cases under `contracts/`; 
- `docs/authoring.md`, `docs/benchmark-design.md`, `docs/task-format.md`;
- corpus manifest/version artifacts introduced by Plan 001.

**Out of scope**:

- Adding subjective LLM grading.
- Changing starter difficulty merely to alter pass rates.
- Retrofactively changing historical result artifacts.
- Partial-credit rubrics; Plan 004 owns them.
- Any site UI work.
- The twelve evaluators not named above without a reproducing fixture.

## Git workflow

- Branch: `advisor/003-repair-evaluator-validity`
- Suggested commits by coherent group, for example:
  `fix: accept equivalent module and shell forms in evaluators`.
- Do not push without authorization.

## Steps

### Step 1: Repair the six documented false-negative paths

For each task, first unskip the Plan 002 passing fixture and confirm it fails.
Then make the smallest semantic repair:

1. **`container-native-vs-oci`**
   - Normalize imported module output with
     `cfg = if module ? config then module.config else module`.
   - Normalize the nested container `config` if it may be a function or attrset;
     provide only public neutral arguments needed for evaluation.
   - Continue rejecting OCI attributes and missing native-container behavior.

2. **`debug-network-false-lead`**
   - Update `prompt.md` with an explicit Nix attrset schema and value vocabulary
     for `physicalLink`, `ipv4.hasAddress`, `ipv4.hasDefaultRoute`,
     `arp.gateway`, `dns.lookup`, and optional audio observations.
   - Prefer structured required facts. If free-form strings remain, check only
     the presence/absence of facts explicitly required by the prompt; accept
     broad paraphrases.
   - Keep multiple hidden input combinations to detect hardcoding.

3. **`devshell-tooling-contract`**
   - Accept multiline shell assignments and
     `extra-experimental-features` forms that semantically enable both features.
   - Strip comments before syntax inspection.
   - Do not accept a comment-only mention or an empty assignment; retain the
     existing rejecting fixtures.

4. **`purity-wrapper-derivation`**
   - Allow single- or double-quoted interpolation around the provided Bash path.
   - Keep semantic checks for `makeWrapper`, `lib.makeBinPath [ coreutils ]`,
     impurity exclusions, and `passthru.pure`.

5. **`package-python-application`**
   - Accept runtime dependencies supplied through the current supported
     `dependencies` attribute or `propagatedBuildInputs`.
   - Use opaque package sentinels so string names cannot satisfy the check.
   - Do not accept packages found only in test/build inputs.

6. **`rust-no-network-build`**
   - Add a realistic opaque `lib.getLib` implementation to the fake library.
   - Accept both direct `${onnxruntime}/lib/...` and
     `${lib.getLib onnxruntime}/lib/...` paths.
   - Retain checks against network commands, URLs in active phases, sandbox
     weakening, and unpinned model assets.

**Verify after each task**:
run its passing and rejecting fixture subset; both must have expected outcomes.
At the end, `tests.test_evaluator_contracts` must have no skips for these six.

### Step 2: Repair module and overlay normalization defects

1. **`module-stale-option-migration`**: normalize explicit `config` and valid
   top-level NixOS option shorthand; continue rejecting stale option paths.
2. **`module-system-boundaries`**: accept module attrsets or functions and
   order-independent package collections; test containment and separation, not
   the reference's exact shape.
3. **`module-service-options`**: accept equivalent shell quoting around
   `extraArgs`; retain semantic option type, conditional config, service, and
   firewall checks.
4. **`overlay-module-boundary`**:
   - accept supported `hash` or `sha256` fixed-output forms when the prompt does
     not require one spelling;
   - normalize explicit `config.systemd` and top-level module shorthand;
   - preserve the package/module separation and runtime input assertions.
5. **`xdg-portal-merge`**: require the Hyprland portal package in the effective
   portal package set, not specifically `configPackages` unless the prompt is
   changed to require that exact field; retain fallback-preservation checks.

**Verify**:
module/overlay pass fixtures exercise both normalized representations; invalid
fixtures still reject cross-module leakage, stale paths, and replacement of
existing values.

### Step 3: Repair packaging and syntax-inspection defects

1. **`fhs-binary-wrapper`**: remove exact root-attribute allowlisting. Check
   targeted forbidden host-mutation behavior while allowing unrelated metadata
   and passthru values.
2. **`python-cuda-uv2nix-patch`**: accept supported runtime dependency
   attributes exactly as in the Python application repair.
3. **`string-escaping-systemd`**: accept `bash -c` and `bash -lc` unless login
   shell behavior is made an explicit requirement. Continue checking that the
   runtime shell variable survives Nix interpolation and output is appended.
4. **`home-manager-xdg-files`**: inspect only relevant activation/file option
   fields rather than JSON-string-scanning unrelated values. Keep explicit
   rejection of imperative directory/symlink setup in active implementation
   fields.

**Verify**:
add one valid quoting/metadata/unrelated-text fixture and one targeted forbidden
implementation fixture per task.

### Step 4: Repair prose and broad-prohibition tasks

1. **`issue-report-quality`**
   - Keep the output structured.
   - Grade required fields, nonempty concrete command/reproduction data,
     internal consistency, and explicit uncertainty fields.
   - Stop requiring particular prose keywords when multiple clear paraphrases
     exist.
   - Add at least three structurally different valid reports and invalid reports
     for missing reproduction, contradicted actual/expected behavior, and
     unsupported certainty.
   - If deterministic semantics cannot distinguish a good report from keyword
     matching, narrow the task's public schema rather than adding more regexes.

2. **`mutable-config-home-manager`**
   - Detect any managed `home.file` or equivalent target nested under the
     Thunderbird mutable profile root, not just the reference profile name and
     two known files.
   - Preserve unrelated managed files and declarative policies.
   - Add a second hidden profile path and a deceptive nested target fixture.

**Verify**:
valid paraphrases and unrelated managed files pass; unsupported certainty and
arbitrary managed profile state fail.

### Step 5: Enforce zero known-issue skips and record decisions

Remove every `known_issue = "plan-003"` marker. Add a test that fails if any
contract fixture is skipped because of evaluator behavior. Test-framework skips
such as “Nix is unavailable” may remain.

For each repaired evaluator, add a short comment only where the normalization
choice is nonobvious. Update authoring docs with the rule:

> Hidden cases may vary inputs and expose edge conditions. Hidden evaluators may
> not require an undocumented representation when common semantic alternatives
> exist.

**Verify**:
`set -o pipefail; python3 -m unittest tests.test_evaluator_contracts -v 2>&1 | tee /tmp/contracts.log && ! grep -q 'known_issue' /tmp/contracts.log`
→ exit 0; test failures cannot be masked by `tee`.

### Step 6: Version the changed corpus

Use Plan 001's corpus tooling to compute the new digest, but keep the version at
`2.0.0-dev`. Record a draft release note listing the evaluator repairs. Plan 004
finalizes `2.0.0` only after rubric migration, so no public 2.0.0 trials exist
with binary scoring. The draft release note must list:

- tasks with prompt changes;
- tasks with evaluator-only semantic normalization;
- why old and new trial totals must not be pooled;
- that historical results remain unmodified.

Do not run or publish new model trials in this plan.

**Verify**:
`python3 bench.py corpus-id --json`
→ new version and digest differ from the pre-repair identity.

### Step 7: Run complete verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: all tests pass; zero contract skips; 29/29 references full-score;
29/29 starters cleanly rejected.

## Test plan

- Every repaired defect has an independently authored valid regression.
- Every relaxation has a nearby invalid fixture proving it did not become a
  no-op.
- Module forms, list ordering, shell quoting, modern dependency attributes, and
  fake-library helpers are tested through semantic outputs where possible.
- Prose checks test structure and consistency rather than reference keywords.
- Full corpus smoke checks still hold.

## Done criteria

- [x] All six published caveat candidates pass.
- [x] All eleven additional defects have targeted tests and repairs.
- [x] No evaluator contract case is skipped for a known evaluator defect.
- [x] All 29 tasks retain pass and reject fixture coverage.
- [x] Corpus version/digest changed and release notes explain incompatibility.
- [x] Historical results are untouched.
- [x] Full verification passes.
- [x] No site UI files changed.
- [x] `plans/README.md` marks Plan 003 DONE.

## STOP conditions

- A proposed relaxation allows an existing targeted invalid fixture to pass.
- A requirement cannot be graded objectively without an LLM judge. Narrow or
  restructure the public task and report the benchmark-semantic change.
- A fake evaluator would need to emulate a large fraction of nixpkgs to accept
  common solutions. Propose a separate real-build/slow-profile task instead.
- The repair would require retroactively rewriting published result artifacts.

## Maintenance notes

Treat evaluator code as benchmark product code, not disposable shell. Future
real model failures that reveal a plausible valid alternative should become a
passing fixture before any evaluator edit. Do not rescore old trials under new
evaluators; rerun configurations on the new corpus identity.
