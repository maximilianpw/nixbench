# Plan 001: Make corpus and agent configurations content-addressed

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If a
> STOP condition occurs, stop and report; do not improvise. When complete,
> update this plan's row in `plans/README.md`.
>
> **Drift check (run first)**:
> `git diff --stat e2716e6 -- nixbench/cli.py nixbench/export.py nixbench/study.py nixbench/task.py tests docs scripts corpus.toml protocols; git status --short -- nixbench tests docs scripts corpus.toml protocols`
> This checks committed, staged, unstaged, and untracked work. If an in-scope
> file changed, compare this plan with the live implementation before editing.
> Material schema drift is a STOP condition.

## Status

- **Status**: DONE
- **Priority**: P1
- **Effort**: L
- **Risk**: MED
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `e2716e6`, 2026-09-16

## Why this matters

NixBench currently groups studies using `series`, `effort`, and task count. Two
runs with different evaluators, prompts, agent versions, timeouts, or execution
protocols can therefore be pooled as one configuration. Conversely, unrelated
site-only commits change `corpus_revision` even when task content is identical.
Before any evaluator behavior changes, corpus and configuration identity must
be derived from the content and protocol that actually produced a result.

## Current state

- `nixbench/cli.py:172-189` records model, effort, agent kind/version, network,
  host, platform, git revision, and timeout as loose metadata.
- `nixbench/cli.py:263-273` obtains `corpus_revision` with `git rev-parse HEAD`;
  it is not a task-content identity and is not dirty-aware.
- `nixbench/study.py:126-130` verifies only equal task counts across trials.
- `nixbench/study.py:189-197` counts replicates by series, effort, and task
  count.
- `nixbench/export.py:74-76` builds a configuration ID as
  `series-effort-task_count`.
- Existing JSON fields and CLI flags are consumed by the current site and run
  scripts. Preserve them as compatibility/display fields; do not use them as
  authoritative identity.

Use deep modules with small interfaces:

- `nixbench/corpus.py`: compute and validate corpus manifests/digests.
- `nixbench/protocol.py`: load a run protocol and derive configuration identity.
- Callers should not reimplement hashing or canonicalization.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Syntax | `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py` | exit 0 |
| Unit tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_task_loading tests.test_runner tests.test_export tests.test_cli -v` | all pass |
| Full tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | all pass |
| Corpus validation | `python3 bench.py validate --solution reference` | 29/29 expected passes |

## Scope

**In scope**:

- `nixbench/corpus.py` (new)
- `nixbench/protocol.py` (new)
- `nixbench/cli.py`
- `nixbench/study.py`
- `nixbench/export.py`
- `nixbench/task.py` only if a task-relative file inventory helper belongs there
- `tests/test_corpus_identity.py` (new)
- `tests/test_protocol.py` (new)
- focused additions to `tests/test_cli.py`, `tests/test_runner.py`, and
  `tests/test_export.py`
- `corpus.toml` (new)
- `protocols/example.toml` (new, contains no credentials or machine-local paths)
- `docs/reproducibility.md`, `docs/running-agents.md`, `docs/task-format.md`
- `scripts/run-current-studies.sh` if it exists and still keys resumption by task count

**Out of scope**:

- Any task prompt, starter, reference, or evaluator.
- Partial scoring and failure-class semantics; Plan 004 owns those.
- Statistical formulas and task-level reporting; Plan 005 owns those.
- Site components, charts, CSS, or page copy.
- Publishing, pushing, or creating a private repository.

## Git workflow

- Branch: `advisor/001-content-addressed-identities`
- Use conventional commits, matching recent history, for example:
  `feat: add content-addressed corpus identity`.
- Do not push or open a pull request without explicit authorization.

## Steps

### Step 1: Define a canonical corpus manifest and digest

Create `corpus.toml` with human-maintained identity fields only. Use one
unreleased major version through Plans 001–004; Plan 003 finalizes the same
version rather than bumping it again:

```toml
schema_version = 1
id = "nixbench-public"
version = "2.0.0-dev"
visibility = "public"
```

Do **not** hand-maintain a digest in this source file. In `nixbench/corpus.py`,
add an immutable `CorpusIdentity` value and one public function such as:

```python
def identify_corpus(tasks_dir: Path, manifest_path: Path | None = None) -> CorpusIdentity: ...
```

The digest must be SHA-256 over a deterministic stream containing:

1. manifest schema/id/version/visibility;
2. tasks sorted by task ID;
3. each task's relative path, executable-mode bit, and bytes for
   `metadata.toml`, `prompt.md`, every regular file or symlink descriptor under
   `starter/`, `reference/`, and `tests/`;
4. corpus-owned evaluator contract fixtures under `contracts/`, when present.

Include path separators, file-kind markers, executable-mode bits, and byte
lengths in the hash stream to prevent concatenation ambiguity. Reject files
that escape the corpus via symlinks. The identity must include task count,
sorted task IDs, and a per-task digest computed with the same canonical rules;
Plan 005 uses those task digests for longitudinal analysis. Git state must not
change the digest.

**Verify**:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_corpus_identity -v`
→ tests prove stable ordering, content sensitivity, site-file insensitivity,
external-corpus support, and symlink rejection.

### Step 2: Add an inspectable corpus identity command

Add `bench.py corpus-id` with optional `--json`. It should print corpus ID,
version, visibility, digest, and task count for `--tasks-dir`. Keep
`corpus_revision` as provenance, but add `corpus_id`, `corpus_version`, and
`corpus_digest` to run/study metadata.

The command must work when `--tasks-dir` is outside a Git repository.

**Verify**:
`python3 bench.py corpus-id --json | python3 -m json.tool`
→ exit 0 and output includes `id`, `version`, `visibility`, `digest`, and
`task_count: 29`.

### Step 3: Define a canonical run protocol

Create `nixbench/protocol.py` and `protocols/example.toml`. The protocol is the
configuration's controlled interface, separate from display labels. Support at
least:

- `schema_version`
- `id` (human-readable profile ID)
- `harness_id` and `harness_version`
- `model_id`
- `model_identity_evidence`: one of `vendor-api-direct`, `router-alias`,
  `local-weights-sha256`, or `unverified`
- `effort`
- `network_policy`
- `isolation_profile`
- `tool_policy`
- `agent_timeout_seconds`
- `system`

Add `--wrapper-prompt-file` alongside `--protocol-file`. The harness must read
the exact wrapper prompt bytes itself and hash them. It must also hash the exact
`--agent-cmd` string it executes. Store the derived `wrapper_prompt_sha256` and
`agent_command_sha256` in the resolved protocol; do not accept self-asserted
hash values from TOML. If a launcher adapter constructs the final command, its
trusted adapter must return the exact executed command descriptor for hashing.

Never require raw credentials or environment values. Expose only hashes in
publication metadata. Derive `configuration_id` from canonical JSON containing
the resolved protocol fields plus `corpus_digest`. Keep `series`, `marker`, and
`label` as display-only data.
Host must be recorded but excluded from correctness identity; derive a separate
`timing_environment_id` from host/platform/system/isolation if timing is later
aggregated.

Add `--protocol-file` to `run-all`. For backward compatibility, runs without a
protocol file may proceed but must be marked `protocol_complete = false` and
must not pass the publication gate in `export-site` unless an explicit
`--allow-legacy-protocol` flag is supplied.

**Verify**:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_protocol tests.test_cli -v`
→ equivalent TOML key order produces the same ID; changed timeout, wrapper
prompt, model, harness version, or corpus digest changes it; display labels do
not.

### Step 4: Prevent heterogeneous trials from being pooled

Update study creation and counting so all trials in one study must share the
same `corpus_digest` and `configuration_id`. Replace task-count-based replicate
counting with these identities while retaining the old parameters only as a
clearly deprecated compatibility path.

Update `export-site` to:

- use stored `configuration_id` rather than constructing one from display data;
- reject mixed corpus digests or protocol identities;
- export corpus ID/version/digest and protocol/timing IDs;
- preserve existing fields so current consumers continue to load;
- refuse legacy identity by default, with the explicit compatibility flag above.

Do not silently rewrite existing checked data. Tests should build legacy and
new fixtures and prove they cannot merge accidentally.

**Verify**:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_runner tests.test_export -v`
→ mixed identities are rejected and homogeneous studies export successfully.

### Step 5: Document the identity contract

Update reproducibility and running docs to state:

- corpus digest identifies benchmark content; Git revision is provenance only;
- configuration identity describes the complete agent protocol, not merely the
  model name;
- model identity evidence can be an unverified router alias;
- timing comparisons require matching timing environment IDs;
- changing any prompt, starter, reference, evaluator, rubric, or task metadata
  creates a new corpus digest and may require a version bump.

Update examples to use `--protocol-file`. Do not make visual website changes.

**Verify**:
`grep -R "series-effort-task" -n nixbench tests docs scripts || true`
→ no live code relies on the old identity formula; any documentation mention is
explicitly historical/deprecated.

### Step 6: Run complete verification

Run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py tests/*.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

Expected: syntax and tests pass; all 29 references receive full score; all 29
starters are clean evaluator rejections.

## Test plan

- Corpus digest is deterministic across directory enumeration order.
- Editing task content changes the digest; editing `site/` does not.
- External non-Git task directories work.
- Protocol canonicalization is deterministic.
- Every behavior-affecting protocol field changes configuration ID.
- Display-only metadata does not change configuration ID.
- Mixed corpus/configuration trials are rejected by study and export code.
- Legacy rows remain readable only through an explicit compatibility path.
- No raw agent command is added to exported/public metadata.

## Done criteria

- [x] `corpus.toml` and the two identity modules exist.
- [x] `bench.py corpus-id --json` reports the 29-task corpus deterministically.
- [x] New studies store corpus and configuration IDs.
- [x] Publication/export refuses heterogeneous or incomplete protocols by default.
- [x] Existing display fields remain available for compatibility.
- [x] Full Python and corpus test commands pass.
- [x] No task files or site UI files changed.
- [x] `plans/README.md` marks Plan 001 DONE.

## STOP conditions

- A required identity field would expose a credential, bearer token, cookie, or
  machine secret. Store a one-way hash or redacted descriptor instead.
- Supporting external corpora requires weakening existing task path/symlink
  protections.
- Existing checked data cannot remain readable without silently pooling
  incompatible runs. Stop and propose an explicit migration instead.
- An in-scope schema has materially changed since `e2716e6`.

## Maintenance notes

Corpus digest code becomes measurement-critical. Review canonicalization,
relative-path handling, symlink behavior, and compatibility tests carefully.
Future site or reporting work must group by `configuration_id` and
`corpus_digest`; `series`, labels, task count, and Git revision are not valid
substitutes.
