# NixBench

NixBench is a benchmark for measuring how well AI coding agents write, repair, and reason about Nix code.

The benchmark is intentionally agentic. A model is not asked to produce a single snippet in isolation. Instead, it receives a small broken or incomplete Nix project, edits files in a temporary working directory, and is judged by hidden evaluators. This better matches how people use coding agents in real repositories: inspect the prompt, edit the code, run checks, recover from errors, and leave behind a concrete diff.

## Why This Exists

Nix is a good stress test for AI coding systems because it combines several failure modes that are easy to hide in normal benchmarks:

- It has a small syntax surface but a deep semantic model.
- Correct code often depends on laziness, attrset recursion, and evaluation order.
- Idiomatic Nix frequently uses higher-order functions, overlays, modules, and fixed-output fetchers.
- Many wrong answers look plausible until evaluated.
- Agents often overfit on common nixpkgs patterns and accidentally use helpers that are absent in smaller fake evaluators.

NixBench is built to catch those issues with objective tests.

## What It Measures

The initial corpus covers ten self-contained tasks:

| Task | Area | Difficulty | What It Tests |
|---|---|---:|---|
| `debug-infinite-recursion` | Debugging | Easy | Repairing recursive attrsets without changing the intended output |
| `devshell-tooling-contract` | Dev shells | Easy | `mkShell`, optional inputs, shell environment setup |
| `fetcher-source-pin` | Fetchers | Easy | Commit pinning, SRI hashes, source fetcher shape |
| `flake-per-system-outputs` | Flakes | Medium | Per-system outputs, apps, checks, devShells, and shared helpers |
| `lang-attrsets-normalize` | Nix language | Easy | Attrset traversal, filtering, defaulting, system support |
| `module-service-options` | NixOS modules | Hard | Options, types, `mkIf`, service config, firewall config |
| `overlay-override-package` | Overlays | Hard | `overrideAttrs`, metadata preservation, final vs prev |
| `package-python-application` | Packaging | Medium | Python application packaging contracts |
| `package-stdenv-cli` | Packaging | Medium | `stdenv.mkDerivation`, phases, native tools, metadata |
| `purity-wrapper-derivation` | Purity | Medium | Avoiding host paths and environment impurities |

Most tasks use fake `lib`, fake builders, or fake package sets in the evaluator. That keeps the benchmark fast, deterministic, and focused on Nix structure rather than network access or large builds.

## Repository Layout

```text
.
  bench.py                 # CLI entry point
  nixbench/                # Python harness package
    cli.py
    runner.py
    task.py
  tasks/                   # benchmark corpus
    <task-id>/
      metadata.toml
      prompt.md
      starter/
      reference/
      tests/check.sh
  docs/                    # design and authoring docs
  tests/                   # Python unit tests for the harness
  flake.nix                # development shell and package wrapper
```

## Quick Start

List tasks:

```sh
python3 bench.py list
```

Validate the reference solutions:

```sh
python3 bench.py validate --solution reference
```

Check that the starters fail:

```sh
python3 bench.py validate --solution starter
```

Run one task with an agent:

```sh
python3 bench.py run package-stdenv-cli \
  --agent-cmd 'your-agent-command-here'
```

Run the whole corpus:

```sh
python3 bench.py run-all \
  --agent-cmd 'your-agent-command-here'
```

## Running With Codex

Example Codex command:

```sh
python3 bench.py run-all \
  --agent-timeout-seconds 240 \
  --agent-cmd 'codex -a never exec --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

The agent command is executed inside a copied starter directory. The hidden evaluator is outside that directory and runs only after the agent exits.

For more details, see [Running Agents](docs/running-agents.md).

## How A Task Runs

For each task, the harness:

1. Creates a temporary work directory.
2. Copies `starter/` into that work directory.
3. Copies `prompt.md` as `NIXBENCH_PROMPT.md`.
4. Runs the agent command with the work directory as `cwd`.
5. Runs the hidden evaluator from `tests/check.sh`.
6. Writes logs, a diff, and structured JSON results.
7. Removes the work directory unless `--keep-workdir` is set.

The agent never needs to know where the hidden tests are. It only needs to satisfy the public prompt.

## Agent Environment

The harness sets these environment variables for both the agent command and evaluator:

| Variable | Meaning |
|---|---|
| `NIXBENCH_TASK_ID` | Task id |
| `NIXBENCH_TASK_DIR` | Original task directory |
| `NIXBENCH_WORKDIR` | Temporary editable work directory |
| `NIXBENCH_PROMPT` | Copied prompt path inside the work directory |
| `NIXBENCH_SCORE_FILE` | Optional score file path for partial-credit evaluators |

## Results

Results are written to:

```text
results/<run-id>/<task-id>/
  agent.log
  check.log
  diff.patch
  result.json
results/<run-id>/summary.json
```

Important files:

- `agent.log`: stdout and stderr from the agent.
- `check.log`: stdout and stderr from the hidden evaluator.
- `diff.patch`: diff between the starter and the final agent-edited workdir.
- `result.json`: task-level score and timing.
- `summary.json`: aggregate score for the run.

Example result row:

```json
{
  "task_id": "package-stdenv-cli",
  "passed": true,
  "score": 100.0,
  "max_score": 100.0,
  "solution_mode": "agent"
}
```

## Scoring Model

The default scoring model is strict:

- evaluator exits `0`: full task score
- evaluator exits non-zero: zero
- agent timeout: zero unless the evaluator supplies partial credit

Evaluators can write partial-credit JSON to `$NIXBENCH_SCORE_FILE`:

```json
{
  "score": 70,
  "notes": [
    "flake outputs evaluate",
    "app metadata is missing"
  ]
}
```

The recommended rubric for larger tasks is:

- 70% functional correctness
- 15% Nix idiom
- 10% maintainability
- 5% formatting and lint

See [Scoring](docs/scoring.md).

## Task Format

Each task is a directory:

```text
tasks/<task-id>/
  metadata.toml
  prompt.md
  starter/
  reference/
  tests/check.sh
```

The reference solution is used to validate that a task is internally consistent:

```sh
python3 bench.py validate --solution reference
```

The starter baseline is used to confirm that the task is non-trivial:

```sh
python3 bench.py validate --solution starter
```

See [Task Format](docs/task-format.md) and [Authoring Tasks](docs/authoring.md).

## Design Principles

NixBench tasks should be:

- Small enough for repeated benchmark runs.
- Objective enough to score without LLM judging.
- Hard enough that placeholder code fails.
- Hidden-test friendly.
- Mostly independent of network access.
- Focused on Nix reasoning, not package trivia.

The benchmark is not trying to answer every possible Nix question. It is trying to expose whether an AI agent can produce evaluable Nix code under realistic constraints.

See [Benchmark Design](docs/benchmark-design.md).

## Development

Run Python unit tests:

```sh
python3 -m unittest discover -s tests
```

Validate the reference corpus:

```sh
python3 bench.py validate --solution reference
```

Validate that starters fail:

```sh
python3 bench.py validate --solution starter
```

Compile the harness:

```sh
python3 -m py_compile bench.py nixbench/*.py
```

Enter the Nix dev shell:

```sh
nix develop
```

Format Nix files when `nixfmt-rfc-style` is available:

```sh
nixfmt-rfc-style flake.nix tasks/*/starter/*.nix tasks/*/reference/*.nix
```

This repo also works with Alejandra:

```sh
alejandra flake.nix tasks/*/starter/*.nix tasks/*/reference/*.nix
```

## Limitations

Current limitations:

- The initial corpus is small.
- Scoring is mostly pass/fail.
- No leaderboard service exists yet.
- The harness does not isolate agents with containers or VMs.
- Some task prompts are intentionally narrow because the benchmark is young.

Good next steps:

- Add real-build packaging tasks behind an optional slow profile.
- Add partial-credit evaluators.
- Add a result report generator.
- Add repeated-run support for measuring variance.
- Add corpus versioning and task deprecation policy.

## Documentation

- [Benchmark Design](docs/benchmark-design.md)
- [Running Agents](docs/running-agents.md)
- [Task Format](docs/task-format.md)
- [Authoring Tasks](docs/authoring.md)
- [Scoring](docs/scoring.md)
- [Reproducibility](docs/reproducibility.md)

