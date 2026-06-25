# 2026-06-24 Model Comparison Runs

These are local NixBench runs against the full 24-task corpus.

The raw `results/` artifacts are intentionally not tracked because they contain logs, temporary diffs, and machine-local paths. This document records the durable statistics needed for comparison.

The Claude Opus 4.8 run was started on June 24 and completed on June 25 by running the five missing tail tasks into the same run ID, then regenerating `summary.json`.

## Summary

| Agent | Model | Run ID | Status | Score | Passed | Failed | Timeout Count | Agent Time |
|---|---|---|---|---:|---:|---:|---:|---:|
| Codex CLI | `gpt-5.5` | `20260624T182835Z-4ad8b555` | complete | 2000/2400 | 20 | 4 | 0 | 37m 38s |
| Codex CLI | `gpt-5.4` | `20260624T190640Z-fa04a19c` | complete | 1900/2400 | 19 | 5 | 0 | 36m 45s |
| Codex CLI | `gpt-5.4-mini` | `20260624T194359Z-268b0abe` | complete | 1700/2400 | 17 | 7 | 3 | 36m 50s |
| Claude Code | `claude-opus-4-8` | `20260624T202141Z-881ef1e9` | complete | 1900/2400 | 19 | 5 | 0 | 22m 38s |

All runs used a 240 second per-task agent timeout and the same task prompt contract: read `NIXBENCH_PROMPT.md`, edit only the copied task workdir, do not inspect hidden evaluators, run local checks if useful, then stop.

## Per-Task Results

| Task | GPT-5.5 | GPT-5.4 | GPT-5.4 mini | Claude Opus 4.8 |
|---|---:|---:|---:|---:|
| `container-native-vs-oci` | FAIL | FAIL | FAIL | FAIL |
| `debug-infinite-recursion` | PASS | PASS | PASS | PASS |
| `debug-network-false-lead` | FAIL | FAIL | FAIL | FAIL |
| `devshell-tooling-contract` | PASS | PASS | PASS | PASS |
| `fetcher-source-pin` | PASS | PASS | PASS | PASS |
| `fhs-binary-wrapper` | PASS | PASS | PASS | PASS |
| `flake-input-package-selection` | PASS | PASS | PASS | PASS |
| `flake-per-system-outputs` | PASS | PASS | FAIL | PASS |
| `home-manager-wsl-module-import` | PASS | PASS | PASS | PASS |
| `home-manager-xdg-files` | PASS | PASS | PASS | PASS |
| `issue-report-quality` | FAIL | FAIL | FAIL | FAIL |
| `lang-attrsets-normalize` | PASS | PASS | PASS | PASS |
| `module-path-composition` | PASS | PASS | PASS | PASS |
| `module-service-options` | FAIL | PASS | PASS | PASS |
| `module-stale-option-migration` | PASS | PASS | PASS | PASS |
| `module-system-boundaries` | PASS | PASS | PASS | PASS |
| `mutable-config-home-manager` | PASS | PASS | PASS | PASS |
| `overlay-override-package` | PASS | PASS | PASS | PASS |
| `package-name-lookup-contract` | PASS | PASS | PASS | PASS |
| `package-python-application` | PASS | FAIL | FAIL | PASS |
| `package-stdenv-cli` | PASS | FAIL | FAIL | FAIL |
| `purity-wrapper-derivation` | PASS | PASS | PASS | PASS |
| `python-cuda-uv2nix-patch` | PASS | PASS | PASS | PASS |
| `string-escaping-systemd` | PASS | PASS | FAIL | FAIL |

## Failure Notes

### Shared Misses

| Task | Notes |
|---|---|
| `container-native-vs-oci` | Failed in every completed run. This is the clearest common failure in this comparison. |
| `debug-network-false-lead` | Failed in every run, with GPT-5.4 mini timing out. |
| `issue-report-quality` | Failed in every run that reached it. |

### Model Splits

| Task | Notes |
|---|---|
| `module-service-options` | GPT-5.5 failed; GPT-5.4, GPT-5.4 mini, and Claude Opus 4.8 passed. |
| `flake-per-system-outputs` | GPT-5.4 mini failed by timeout; GPT-5.5, GPT-5.4, and Claude Opus 4.8 passed. |
| `package-python-application` | GPT-5.5 and Claude Opus 4.8 passed; GPT-5.4 and GPT-5.4 mini failed. |
| `package-stdenv-cli` | GPT-5.5 passed; GPT-5.4, GPT-5.4 mini, and Claude Opus 4.8 failed. |
| `string-escaping-systemd` | GPT-5.5 and GPT-5.4 passed; GPT-5.4 mini and Claude Opus 4.8 failed. |

## Commands

GPT-5.5:

```sh
python3 -u bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'codex --ask-for-approval never exec -m gpt-5.5 --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

GPT-5.4:

```sh
python3 -u bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'codex --ask-for-approval never exec -m gpt-5.4 --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

GPT-5.4 mini:

```sh
python3 -u bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'codex --ask-for-approval never exec -m gpt-5.4-mini --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

Claude Opus 4.8:

```sh
python3 -u bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'claude -p --no-session-persistence --permission-mode bypassPermissions --model claude-opus-4-8 "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

The Claude command was initially interrupted with `Ctrl-C` after `package-name-lookup-contract` completed. The remaining five tasks were later run with the same agent command into `20260624T202141Z-881ef1e9`, and the run summary was regenerated from all 24 task result files.
