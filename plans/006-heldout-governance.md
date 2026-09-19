# Plan 006: Build release gates and held-out corpus infrastructure

> **Executor instructions**: This plan implements public repository tooling and
> governance for held-out corpora. It must not author active private tasks in
> this public worktree. Do not create, publish, or push a private repository
> without explicit operator authorization. The first private release receives
> its own plan inside the authorized private repository so its task briefs do
> not leak here.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- nixbench tests docs .github/workflows corpus.toml corpus protocols launchers scripts; git status --short -- nixbench tests docs .github corpus.toml corpus protocols launchers scripts`
> This includes committed and local work. Plans 001–005 are expected to have
> changed these areas. Reconcile live schema versions and commands before
> proceeding.

## Status

- **Status**: DONE
- **Priority**: P2
- **Effort**: L
- **Risk**: MED
- **Depends on**: `plans/001-content-addressed-identities.md`,
  `plans/002-fixture-evaluator-contracts.md`,
  `plans/004-rubric-scoring-validity.md`,
  `plans/005-calibrated-reporting.md`
- **Category**: tech-debt
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

The complete public corpus—including prompts, references, and evaluators—is
inspectable and may enter future model training. It is excellent as a public
development and reproducibility corpus, but it cannot remain the sole basis for
strong leaderboard claims. Corpus release decisions are also currently prose
and convention rather than machine-enforced gates. This plan formalizes public
and held-out roles, release/version/deprecation policy, calibration, rotation,
and redacted publication artifacts.

## Current state

- `docs/reproducibility.md` recommends a private hidden corpus for public
  leaderboards, but none is represented in repository tooling.
- `README.md` and `tasks/` expose all current tasks, reference solutions, and
  evaluators.
- Corpus health currently verifies reference pass and starter fail; Plans 002,
  004, and 005 add contract, rubric, and health data.
- Category distribution is uneven: modules and packages account for 15/29
  tasks, while devshells, fetchers, and purity have one task each.
- Difficulty labels are author judgments; empirical calibration is not yet a
  release gate.
- External corpora are already conceptually supported by `--tasks-dir`; Plan
  001 makes their identity content-addressed, and this plan packages tasks plus
  contracts under a single `--corpus-root` for release checks.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Release check | `python3 bench.py release-check --corpus-root . --json` | `eligible: true` for a healthy corpus |
| Public tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |
| Corpus checks | `python3 bench.py validate --solution reference && python3 bench.py validate --solution starter` | expected outcomes |
| Private check | `python3 bench.py release-check --corpus-root "$PRIVATE_NIXBENCH_CORPUS" --json` | eligible without exposing task content |

## Scope

**Public repository phase — in scope**:

- `nixbench/release.py` (new) or equivalent focused module
- `nixbench/isolation.py` (new trusted launcher/isolation interface)
- `nixbench/cli.py`
- `nixbench/corpus.py`, scoring/reporting modules only as needed to consume
  their established interfaces
- `tests/test_release.py` (new)
- `.github/workflows/tests.yml`
- `docs/benchmark-governance.md` (new)
- `docs/reproducibility.md`, `docs/authoring.md`, `docs/task-format.md`, README
- `corpus/releases/<version>.json` checked release manifests
- `corpus/category-vocabulary.toml` (new)
- `corpus/task-deprecations.toml` (new)
- `launchers/` profiles and trusted wrapper scripts for isolated execution
- optional `scripts/init-private-corpus.py` that creates a local template but
  never uploads it

**Out of scope**:

- Site visual design.
- Publishing private prompts, references, evaluator sources, logs, or task IDs.
- Claiming private tasks are contamination-proof forever.
- Automatically changing corpus composition based solely on model results.
- Pushing, deploying, or creating remote infrastructure without authorization.
- Authoring active private task briefs or implementations in this public plan;
  those belong to a plan stored in the authorized private repository.

## Git workflow

- Public branch: `advisor/006-heldout-governance`
- Private work must use a separately authorized branch/repository.
- Suggested public commit: `feat: add benchmark corpus release governance`
- Never commit private task material to this repository, including in Git
  history.

## Steps

### Step 1: Write the benchmark governance policy

Create `docs/benchmark-governance.md` defining:

- **public development corpus**: fully inspectable, reproducible, used for local
  development, evaluator auditing, and transparent diagnostic comparisons;
- **private held-out corpus**: same task/evaluator standards, used for stronger
  comparative claims, stored outside this repository;
- **retired corpus**: formerly held-out tasks published after rotation for
  auditability and research.

Specify versioning:

- patch: docs/harness changes that do not affect task outcome or scoring;
- minor: new tasks added without changing existing contracts, with results
  reported under a new corpus identity;
- major: prompt, starter, evaluator acceptance boundary, rubric, points, or
  required protocol changes.

Specify that historical trials are immutable and never silently pooled across
corpus/configuration IDs.

Define lifecycle states: draft, calibrating, active, quarantined, deprecated,
retired. Quarantined tasks do not contribute to headline scores until repaired
and recalibrated.

**Verify**:
document review tests are not needed, but `release-check --explain` added below
must point to these exact policies.

### Step 2: Implement one release-gate module

Add `bench.py release-check` backed by one module interface. Its input is a
`--corpus-root` containing `corpus.toml`, `tasks/`, `contracts/`, release notes,
and release manifests. The command recomputes health data by default. An explicit `--health-report`
may be used only outside release CI and must match corpus digest, scoring schema,
report schema/method versions, and the current release-tool implementation
digest; stale or unverifiable provenance is rejected. Release CI always
recomputes health evidence. The command does not inspect a run protocol;
run-specific publication eligibility belongs to a separate
`bench.py publication-check --study-path ...` command. For an active corpus
release, require:

- valid corpus manifest/version/digest;
- category from controlled vocabulary;
- reference full score and starter valid rejection;
- at least one passing and one rejecting independent contract fixture per task;
- all required rubric criteria mapped to fixtures;
- evaluator determinism across two reference and representative fixture runs;
- no invalid measurements;
- evaluator runtime below declared timeout with a documented safety margin;
- no active known-issue skips;
- no unrecorded task deprecations;
- a release note describing semantic changes;
- a declaration of which protocol schema version future publication checks
  must require.

`publication-check` must separately require complete configuration identity,
completion attestation, scoring schema, all-valid complete trials, and the
corpus's required protocol schema.

Output JSON with `eligible`, corpus identity, passed/failed gates, and safe
reasons. Do not emit private task content in JSON.

**Verify**:
`tests/test_release.py` uses small fixture corpora to prove each failed gate is
specific and actionable.

### Step 3: Add release manifests and CI enforcement

A checked release manifest under `corpus/releases/<version>.json` must include:

- schema version;
- corpus ID/version/digest/visibility;
- release date;
- task count and category/difficulty counts;
- scoring schema and reporting method versions;
- release-gate result digest computed over canonical JSON of all gate names,
  pass/fail states, evidence digests, tool schema versions, and corpus digest;
  the release manifest itself must not be an input to that digest;
- previous version and compatibility classification;
- added/changed/deprecated task IDs for public corpora; private manifests may
  use opaque stable task hashes instead.

Add CI that runs the release check for the public corpus and verifies the
checked manifest whenever tasks, contracts, scoring/reporting code, category or
deprecation policy, release tooling, or governance docs change. CI must fail if
corpus content or release evidence changes without an updated version/release
manifest.

**Verify**:
change a copied evaluator in a test fixture without changing its manifest;
release check must fail with digest/version mismatch.

### Step 4: Define calibration and balance policy

Use Plan 005's corpus-health report to require a calibration review before a
task becomes active. Record, but do not mechanically enforce without human
review:

- solve rate and uncertainty across at least three materially different agent
  configurations and repeated trials where affordable;
- timeout and invalid-measurement rates;
- discrimination statistic when sample size permits;
- common failure classes;
- evaluator disputes/valid-alternative additions;
- empirical difficulty band separate from author difficulty.

Category policy:

- report every category transparently regardless of size;
- mark categories with fewer than five active tasks descriptive-only;
- prioritize new tasks for underrepresented categories rather than reweighting
  headline scores;
- avoid adding near-duplicate module/package tasks solely to increase corpus
  size.

Initial public-corpus roadmap after correctness work: add enough independent
fetcher, devshell, purity, overlay, language, and debugging tasks to reduce the
current module/package dominance. Author each addition under a minor corpus
version and contract/rubric/release gates.

**Verify**:
release report lists stratum counts and flags under-five categories without
blocking a development release; production held-out policy may choose stricter
minimums.

### Step 5: Add redacted publication bundles

Add a command such as:

```sh
python3 bench.py export-publication \
  --study-id ... \
  --redact-task-details \
  --output publication.json
```

For private corpora, use a strict allowlist and export only:

- corpus ID/version/digest and visibility;
- configuration/protocol identity and model identity evidence;
- whole-corpus aggregate statistics only when at least five active tasks and at
  least twenty valid task-trial observations contribute;
- stratum statistics only under the same five-task/twenty-observation minimum;
- when the whole corpus is below that minimum, only identity/method metadata and
  `insufficient_aggregation = true`—no scores, pass/fail totals, invalid counts,
  timeout counts, or other outcome-bearing values;
- task count and rubric/report method versions only when the task count itself
  is not restricted by the private release policy;
- invalid measurement and timeout counts only when the whole-corpus minimum is
  met;
- no opaque per-task hashes, prompts, filenames, task IDs, references,
  evaluator logs, diffs, agent logs, or per-task outcomes while the corpus is
  active.

Sentinel scanning is defense in depth; the allowlist and suppression thresholds
are the primary inference-leak controls. Apply suppression to the whole corpus
before any subordinate stratum logic so a one-task corpus cannot leak through
its aggregate.

Add a scanner test with sentinel private strings to prove they cannot enter the
redacted bundle. Preserve full raw artifacts only in the authorized private
storage location.

**Verify**:
`tests.test_release` or a new publication test confirms sentinel task content
is absent and schema remains analytically useful.

### Step 6: Enforce trusted filesystem isolation for held-out runs

Recording an `isolation_profile` is insufficient. Add a trusted launcher seam
used by the runner for publishable held-out studies. A launcher profile must
construct the process itself; `--agent-cmd` alone cannot claim held-out
isolation.

Provide a Linux bubblewrap profile matching the repository's documented Astra
run principles:

- copied task workspace mounted read-write at a neutral path;
- fresh writable home and `/tmp`;
- only required system/Nix paths mounted read-only;
- original benchmark repository, corpus root, task tests, references, results,
  host home, and Nix daemon socket absent;
- network policy enforced according to the resolved protocol;
- status-file channel from Plan 004 mounted where only the trusted launcher can
  write it, outside the agent-editable workspace;
- process namespace isolation and process-group cleanup.

Before the model command, run machine-checkable preflights from inside the
sandbox proving the forbidden paths are absent and the workspace is writable.
The launcher writes preflight and completion evidence to the attestation file.
A held-out study is nonpublishable unless `publication-check` verifies an
approved isolation profile, successful preflight, and completion attestation.
Platforms without the approved isolation adapter may run development corpora
but not publish held-out results.

**Verify**:
integration tests use sentinel files in the corpus, reference, evaluator, host
home, and results directory and prove the sandboxed command cannot read them;
it can edit the copied workspace and the evaluator still runs afterward on the
host.

### Step 7: Create a local private-corpus template without publishing it

Provide a script or documented command that initializes a local directory with:

- private `corpus.toml` (`visibility = "private-heldout"`);
- `tasks/` and corpus-owned `contracts/` structure;
- CI sample that runs release checks without uploading artifacts;
- `.gitignore`/security guidance preventing accidental inclusion in this public
  repository;
- rotation and retirement checklist;
- a private `plans/001-first-heldout-release.md` template that requires the
  operator to select task briefs, calibration configurations, repetition count,
  cost budget, and activation/quarantine thresholds before implementation.

The script must refuse a destination inside the public repository and must not
run Git remote commands. The generated private plan, not this public plan, owns
active task specifications and calibration decisions.

**Verify**:
unit/integration test initializes in a temporary directory, passes path safety,
and refuses a nested public-repo path.

### Step 8: Define rotation and disclosure operations

Policy should require:

- periodic addition/rotation, e.g. each major leaderboard cycle or when
  contamination evidence appears;
- no selective replacement based on whether a favored configuration failed;
- retirement decisions recorded before inspecting new comparison results when
  practical;
- retired private tasks moved to a public archive with references and evaluator
  history after they stop contributing to active scores;
- public/private score delta reported as a contamination diagnostic only when
  category composition and protocols are matched;
- no private corpus treated as permanently secret or permanently valid.

Specify that the first private corpus cannot be activated until its private
plan records exact task briefs, chosen calibration configurations, trial count,
budget, and objective quarantine thresholds. Add an operator checklist, not an
automated remote action.

### Step 9: Run public verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py release-check --corpus-root . --json > /tmp/release-check.json
python3 - <<'PY'
import json
with open('/tmp/release-check.json') as handle:
    report = json.load(handle)
assert report['eligible'] is True, report
PY
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: all tests pass; release check explicitly reports `eligible: true`;
reference/starter checks pass.

## Test plan

- Every release gate has a failing fixture and actionable reason.
- Task/scoring content changes invalidate the checked release manifest.
- Category vocabulary and deprecations are validated.
- Trusted isolation prevents access to corpus, evaluator, reference, host-home,
  and result sentinels while allowing copied-workspace edits.
- Private template initialization refuses unsafe/public-repo destinations.
- Redacted publication bundles cannot leak sentinel task content, artifact
  paths, or small-stratum outcomes.
- Public and private identities remain distinct.
- Calibration reports separate author and empirical difficulty.
- No automation creates remotes, pushes, or publishes private content.

## Done criteria

- [x] Governance policy defines public, private, and retired corpus roles.
- [x] `release-check` enforces content, contract, rubric, determinism, and
  version gates; `publication-check` enforces run protocol and validity.
- [x] CI catches unversioned task, contract, scoring, and release-evidence changes.
- [x] Trusted held-out launcher passes filesystem-isolation preflights and tests.
- [x] Redacted publication export has allowlist, suppression, and leakage tests.
- [x] Private-corpus initializer refuses public-repo destinations and creates a
  private first-release plan template.
- [x] Public release check reports `eligible: true`.
- [x] Public tests and corpus checks pass.
- [x] No private task material or site UI files changed.
- [x] `plans/README.md` marks Plan 006 DONE.

## STOP conditions

- Any command would create a remote, push, deploy, or publish private material.
- The approved isolation adapter cannot prove the benchmark repository, hidden
  corpus, evaluator, reference, and host home are absent from the agent sandbox.
- A redacted export contains prompts, task IDs, filenames, logs, diffs, or
  reference/evaluator content from a private corpus.
- Calibration requires changing a task after seeing a particular model's result
  without a predeclared methodological reason.
- Release eligibility would require bypassing an invalid-measurement or contract
  failure.

## Maintenance notes

A private corpus is an operational program, not a one-time directory. Its value
comes from controlled access, rotation, release manifests, calibration, and
honest disclosure. Review public/private score deltas as possible contamination
signals, not proof of memorization. Keep retired tasks auditable and active tasks
unpublished.
