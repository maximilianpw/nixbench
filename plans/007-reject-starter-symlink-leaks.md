# Plan 007: Prevent starter and contract symlinks from exposing hidden corpus content

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` unless a reviewer told you they maintain the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- nixbench/corpus.py nixbench/task.py tests/test_corpus_identity.py tests/test_task_loading.py docs/task-format.md`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

The corpus identity layer permits symlinks whose targets remain anywhere under
the corpus root, while the runner copies starter trees with symlink-following
semantics. A starter symlink can therefore copy a reference solution,
evaluator, contract fixture, or another task into the agent workspace before
isolation starts. Private held-out tasks need a stronger invariant: editable
candidate inputs must not resolve outside their own editable tree.

## Current state

- `nixbench/corpus.py:231-235` accepts any symlink whose target remains inside
  the overall corpus root:

  ```python
  if stat.S_ISLNK(metadata.st_mode):
      target = os.readlink(path)
      resolved_target = (path.parent / target).resolve(strict=False)
      _require_within(resolved_target, corpus_root, f"symlink target for {path}")
      return relative.as_posix(), "symlink", executable, os.fsencode(target)
  ```

- `nixbench/runner.py:130-131` uses default `shutil.copytree` behavior, which
  follows file symlinks and copies the target bytes:

  ```python
  shutil.copytree(task.starter_dir, workdir)
  shutil.copytree(task.starter_dir, original_dir)
  ```

- `tests/test_corpus_identity.py:93-102` explicitly accepts an internal starter
  symlink, but only tests a same-directory target.
- `docs/task-format.md:42-45` promises that required paths may not escape the
  task through symlinks. Tighten this for editable trees rather than weakening
  the documentation.
- Corpus validation uses `ValueError`; task-structure validation uses
  `TaskError`. Match the existing exception family at the boundary where the
  new check is implemented.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Focused tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_corpus_identity tests.test_task_loading -v` | exit 0, all tests pass |
| Full Python suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | exit 0 when Bubblewrap is available; no symlink-related failures |
| Corpus identity | `python3 bench.py corpus-id --json` | exit 0 and a deterministic digest |
| Reference validation | `python3 bench.py validate --solution reference` | 29/29 expected outcomes |
| Starter validation | `python3 bench.py validate --solution starter` | 29/29 expected outcomes |

## Scope

**In scope**:
- `nixbench/corpus.py`
- `nixbench/task.py` only if task-local validation is the cleanest enforcement point
- `tests/test_corpus_identity.py`
- `tests/test_task_loading.py` only if `Task.validate` changes
- `docs/task-format.md`

**Out of scope**:
- `nixbench/runner.py` copying behavior, unless tests prove a defense-in-depth
  change is required after validation is added.
- Reference and evaluator trees. They are trusted corpus-owned inputs and are
  not copied into the agent workspace as editable starter content.
- Existing task semantics, prompts, scores, or contract outcomes.
- Broad filesystem sandbox changes; this plan addresses corpus-tree leakage.

## Git workflow

- Suggested branch: `advisor/007-reject-starter-symlink-leaks`
- Use a focused commit such as `fix: reject escaping starter symlinks`.
- Do not push or open a PR without explicit operator authorization.

## Steps

### Step 1: Add regression tests for hidden-content symlinks

In `tests/test_corpus_identity.py`, add cases proving corpus loading rejects:

1. `tasks/toy/starter/answer.nix -> ../reference/answer.nix`.
2. `tasks/toy/starter/check.sh -> ../tests/check.sh`.
3. A contract candidate symlink whose target leaves that candidate directory,
   including a target elsewhere under the same corpus root.
4. A symlink whose target remains inside the same starter or candidate tree.
   Choose and document one policy:
   - preferred: reject all symlinks in editable starter/candidate trees; or
   - acceptable: allow only targets contained in the same editable tree and
     preserve symlinks during copying.

Prefer the simpler all-symlink rejection policy unless an existing checked task
or fixture relies on a symlink.

**Verify**: run the focused tests before implementation and confirm the new
leak cases fail for the expected reason, not because fixture setup is invalid.

### Step 2: Enforce the editable-tree boundary during corpus identification

Update `_tree_entries`, `_walk_directory`, or a new narrowly named helper in
`nixbench/corpus.py` so the policy is explicit for:

- `tasks/<id>/starter/**`;
- `contracts/<id>/<case>/candidate/**`.

Do not merely require targets to remain in `corpus_root`. The boundary must be
the specific starter or candidate root. Error messages must name the offending
path and state that editable candidate content cannot reference files outside
its editable tree.

Keep canonical hashing deterministic. If all editable-tree symlinks are
rejected, no hashing-format migration is required beyond the corpus digest
changing only when corpus content changes.

**Verify**: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_corpus_identity -v` → all tests pass.

### Step 3: Align task validation and documentation

If `identify_corpus` is the only enforcement boundary, document that corpus
identity/release loading rejects editable-tree symlinks. If `Task.validate`
also enforces the rule, add matching tests in `tests/test_task_loading.py`.

Update `docs/task-format.md` to state the exact policy for starter and contract
candidate symlinks. Do not claim all corpus symlinks are forbidden if reference
or evaluator symlinks remain supported.

**Verify**: `python3 bench.py corpus-id --json` → exit 0 for the current corpus.

### Step 4: Run corpus behavior checks

Run both reference and starter validation. The current repository contains no
intentional editable-tree symlinks, so all 29 tasks should retain their current
outcomes.

**Verify**:

- `python3 bench.py validate --solution reference` → `29/29` matched.
- `python3 bench.py validate --solution starter` → `29/29` matched.

## Test plan

- Reject starter-to-reference symlink.
- Reject starter-to-evaluator symlink.
- Reject candidate-to-neighbor-contract symlink.
- Cover the chosen same-tree policy explicitly.
- Confirm ordinary regular files and current corpus identity still load.
- Use `tests/test_corpus_identity.py` existing temporary-corpus helpers as the
  structural pattern.

## Done criteria

- [ ] Editable starter and contract candidate trees cannot resolve content from outside their own tree.
- [ ] Regression tests cover reference, evaluator, and neighboring-contract targets.
- [ ] `python3 bench.py corpus-id --json` exits 0.
- [ ] Reference validation reports 29/29 expected passes.
- [ ] Starter validation reports 29/29 expected rejections.
- [ ] Documentation states the exact symlink policy.
- [ ] No task prompt, evaluator, score, or reference solution changed.
- [ ] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- Any current task or contract candidate intentionally depends on a symlink.
- Enforcing the boundary requires changing task behavior or evaluator semantics.
- The corpus digest algorithm must be versioned rather than merely producing a
  new digest from changed corpus content.
- Focused tests reveal `copytree` semantics differ from the assumed dereference
  behavior on a supported platform.

## Maintenance notes

Review future corpus features that add generated files, fixtures, or archives
against the same rule: bytes visible to the agent must be owned by and hashed
as part of that task's editable input. A reviewer should specifically reject
"safe because it stays in the corpus root" as an insufficient boundary for
private or held-out corpora.
