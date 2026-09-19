# Task format

Each benchmark task lives in `tasks/<task-id>/`.

```text
tasks/<task-id>/
  metadata.toml
  prompt.md
  starter/
  reference/
  tests/
    check.sh
```

## `metadata.toml`

Required fields:

```toml
id = "package-stdenv-cli"
name = "Package A stdenv CLI"
category = "packages"
difficulty = "medium"
timeout_seconds = 60
max_score = 100
systems = ["any"]
evaluator = "tests/check.sh"

[[criteria]]
id = "package-source"
points = 25
required = true
failure_class = "impurity"
```

`systems = ["any"]` means the task is system-independent. Use Nix system names such as `x86_64-linux` or `aarch64-darwin` for system-specific tasks.

All listed fields are mandatory. Task ids must be lowercase hyphenated slugs,
`difficulty` must be `easy`, `medium`, or `hard`, and `category` must use the
controlled vocabulary in Metadata guidance below. Corpus loading rejects an
unknown category. Timeouts and maximum scores must be positive, and `systems`
must be a non-empty list without duplicates. The evaluator must be a relative
path that resolves inside the task directory. The prompt and evaluator must be
files; `starter/`, `reference/`, and `tests/` must be directories, and required
paths may not escape the task through symlinks. Duplicate task ids are rejected
when loading a corpus.

`corpus/category-vocabulary.toml` is the release-controlled category list.
Changing it requires release review and a new checked gate digest.

Current tasks declare 4 to 8 objective criteria. Criterion IDs are unique
lowercase slugs, points are positive and sum exactly to `max_score`, and every
public prompt requirement maps to a required criterion. See
[scoring.md](scoring.md) for failure classes and compatibility rules.

The corpus manifest lives beside `tasks/` in `corpus.toml`. `python3 bench.py corpus-id --json` computes a SHA-256 digest over the manifest identity fields and all benchmark-owned task content. Paths, file kinds, executable bits, symlink descriptors, and byte lengths are part of the canonical stream. Symlinks may not escape the corpus root.

Changing task metadata, a prompt, starter, reference, evaluator, rubric, or contract fixture changes the corpus digest. A semantic change may also require a corpus version bump. Git revision is recorded separately as provenance and does not define corpus identity.

## `prompt.md`

This is the prompt copied into the workdir as `NIXBENCH_PROMPT.md`. It should describe the task requirements and expected files, but not reveal hidden evaluator details.

## `starter/`

Starter files are copied into a temporary workdir. The agent edits only this copy.

## `reference/`

Reference files are overlaid onto the starter when running:

```sh
python3 bench.py validate --solution reference
```

The reference solution should pass the evaluator and act as a regression fixture for task authors.

## `tests/check.sh`

The evaluator runs as:

```sh
/bin/sh tests/check.sh "$NIXBENCH_WORKDIR"
```

It exits `0` only when every required criterion passes, `1` for a candidate
rejection, and `2` or greater for evaluator infrastructure errors. An ordinary
candidate parse or evaluation error must still write a valid all-false or
partial criterion payload before exiting `1`.

```json
{
  "schema_version": 2,
  "criteria": {
    "package-source": true,
    "build-contract": false
  },
  "notes": ["build contract failed"]
}
```

The payload contains exactly the declared criterion IDs with boolean values.
The harness derives points and failure classes. A missing, malformed, or
scalar payload makes a current task measurement invalid.

`NIXBENCH_SCORE_FILE` is only provided to the evaluator, not to the agent command.
Bundled evaluators use the harness exit helper so exit `0` follows required
criteria only. An optional criterion may fail without rejecting the candidate.

## Authoring checklist

Before adding a task to the corpus:

- Run the reference solution and confirm it passes.
- Run the starter solution and confirm it fails.
- Keep evaluator assertions semantic where possible.
- Add evaluator-contract mutations for at least one invalid candidate and any important valid alternative.
- Give every contract case a declared `criterion_id`, and cover every required criterion.
- Probe functions with more than one input and use opaque fake package values to catch hard-coded outputs.
- Avoid network access in the evaluator unless the task is explicitly marked as a slow integration task.
- Avoid checking only for strings when Nix evaluation can inspect the value.
- Keep prompts clear about required files and expected behavior.
- Record calibration evidence and lifecycle state before activation.
- Update the release note and `corpus/releases/<version>.json`.

## Metadata guidance

Use categories that describe the Nix skill being tested:

- `nix-language`
- `flakes`
- `packages`
- `modules`
- `overlays`
- `fetchers`
- `devshells`
- `debugging`
- `purity`

Use `systems = ["any"]` for pure evaluation tasks. Reserve real Nix systems for tasks that depend on platform-specific behavior.
