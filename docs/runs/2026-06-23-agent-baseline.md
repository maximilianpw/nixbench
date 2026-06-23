# 2026-06-23 Agent Baseline Runs

These are local baseline runs against the initial ten-task NixBench corpus.

The raw `results/` artifacts are intentionally not tracked because they contain logs, temporary diffs, and machine-local paths. This document records the durable statistics needed for comparison.

## Summary

| Agent | Run ID | Score | Passed | Failed | Timeout Count |
|---|---|---:|---:|---:|---:|
| Codex CLI | `20260623T082404Z` | 500/1000 | 5 | 5 | 1 |
| Claude CLI | `20260623T093109Z-b488de64` | 500/1000 | 5 | 5 | 0 |

Both runs used a 240 second per-task agent timeout and the same task prompt contract: read `NIXBENCH_PROMPT.md`, edit only the copied task workdir, do not inspect hidden evaluators, run local checks if useful, then stop.

## Per-Task Results

| Task | Codex | Claude |
|---|---:|---:|
| `debug-infinite-recursion` | PASS | PASS |
| `devshell-tooling-contract` | PASS | PASS |
| `fetcher-source-pin` | PASS | PASS |
| `flake-per-system-outputs` | FAIL | FAIL |
| `lang-attrsets-normalize` | FAIL | FAIL |
| `module-service-options` | FAIL | FAIL |
| `overlay-override-package` | PASS | PASS |
| `package-python-application` | FAIL | FAIL |
| `package-stdenv-cli` | PASS | FAIL |
| `purity-wrapper-derivation` | FAIL | PASS |

## Timing

Agent duration in seconds, as recorded by the harness.

| Task | Codex Seconds | Claude Seconds |
|---|---:|---:|
| `debug-infinite-recursion` | 67.665 | 58.563 |
| `devshell-tooling-contract` | 78.201 | 72.517 |
| `fetcher-source-pin` | 93.000 | 43.614 |
| `flake-per-system-outputs` | 240.022 | 119.600 |
| `lang-attrsets-normalize` | 65.444 | 94.610 |
| `module-service-options` | 125.256 | 121.941 |
| `overlay-override-package` | 47.936 | 37.287 |
| `package-python-application` | 73.938 | 168.967 |
| `package-stdenv-cli` | 176.623 | 43.524 |
| `purity-wrapper-derivation` | 180.345 | 68.109 |

## Failure Notes

### Codex

| Task | Failure |
|---|---|
| `flake-per-system-outputs` | Timed out at 240 seconds; hidden check then found missing `meta.package`. |
| `lang-attrsets-normalize` | Excluded the disabled package from `names`; evaluator expected all names there and filtering only in system package lists. |
| `module-service-options` | Used `lib.escapeShellArgs`, which was absent from the evaluator fake `lib`. |
| `package-python-application` | Used `lib.licenses.mit`; evaluator expected `lib.licenses.asl20`. |
| `purity-wrapper-derivation` | Used `lib.getExe`, which was absent from the evaluator fake `lib`. |

### Claude

| Task | Failure |
|---|---|
| `flake-per-system-outputs` | Missing `meta` attr in the app output. |
| `lang-attrsets-normalize` | Excluded the disabled package from `names`; evaluator expected all names there and filtering only in system package lists. |
| `module-service-options` | Used unavailable `lib.concatStringsSep`. |
| `package-python-application` | Used `lib.licenses.mit`; evaluator expected `lib.licenses.asl20`. |
| `package-stdenv-cli` | Returned a function where the evaluator expected a set. |

## Commands

Codex:

```sh
python3 bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'codex -a never exec --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

Claude:

```sh
python3 bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'claude -p --no-session-persistence --permission-mode bypassPermissions "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

## Interpretation

This is a small local baseline, not a leaderboard. The runs used local CLI defaults, including each tool's default model selection. For serious comparisons, record the exact model, CLI version, NixBench commit, host system, timeout, and repeat count.
