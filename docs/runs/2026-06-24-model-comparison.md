# 2026-06-24 through 2026-07-10 Model Comparison Runs

These are local NixBench runs against the corpus version current on each run date. Historical rows cover 26 tasks; the July 9-10 GPT-5.6 rows cover the expanded 29-task corpus and retain their own denominator in every score.

The raw `results/` artifacts are intentionally not tracked because they contain logs, temporary diffs, and machine-local paths. This document records the durable statistics needed for comparison.

The first comparison on June 24 covered the then-current 24-task corpus. On June 25, `home-manager-extra-special-args` and `overlay-module-boundary` were added to the displayed comparison by running those two tasks separately for each baseline model. Rows marked `(+2)` combine the original 24-task run with those two supplemental task artifacts.

On June 27, `gpt-5.4-mini` was run across the missing low, medium, and high Codex reasoning effort settings.

On June 27 and June 28, Claude Opus 4.8 was run with explicit Claude Code effort settings.

On July 9, GPT-5.6 Sol, Terra, and Luna were each run at xhigh effort against all 29 current tasks using the Codex CLI bundled with the desktop app.

On July 10, the GPT-5.6 effort sweep added low, medium, and high rows for all three models, plus max rows for Sol and Luna. Sol ultra and Terra max/ultra were paused before they started and are not represented below.

## Summary

| Agent | Model | Effort | Run ID | Status | Score | Passed | Failed | Timeout Count | Agent Time |
|---|---|---|---|---|---:|---:|---:|---:|---:|
| Codex CLI | `gpt-5.6-sol` | low | `20260710T080546Z-b5d84e84` | complete | 2100/2900 | 21 | 8 | 0 | 18m 56s |
| Codex CLI | `gpt-5.6-sol` | medium | `20260710T082452Z-0d42d5d1` | complete | 2200/2900 | 22 | 7 | 0 | 27m 24s |
| Codex CLI | `gpt-5.6-sol` | high | `20260710T085227Z-8ce3793d` | complete | 2200/2900 | 22 | 7 | 0 | 30m 15s |
| Codex CLI | `gpt-5.6-sol` | xhigh | `20260709T175817Z-cb86c575` | complete | 2100/2900 | 21 | 8 | 0 | 26m 32s |
| Codex CLI | `gpt-5.6-sol` | max | `20260710T152810Z-214936aa` | complete | 2200/2900 | 22 | 7 | 2 | 47m 54s |
| Codex CLI | `gpt-5.6-terra` | low | `20260710T080604Z-36ff1ac9` | complete | 2000/2900 | 20 | 9 | 0 | 29m 50s |
| Codex CLI | `gpt-5.6-terra` | medium | `20260710T083607Z-086ef952` | complete | 2100/2900 | 21 | 8 | 0 | 33m 14s |
| Codex CLI | `gpt-5.6-terra` | high | `20260710T152820Z-20a86451` | complete | 2100/2900 | 21 | 8 | 0 | 27m 14s |
| Codex CLI | `gpt-5.6-terra` | xhigh | `20260709T175820Z-36a5f2f2` | complete | 1900/2900 | 19 | 10 | 0 | 20m 22s |
| Codex CLI | `gpt-5.6-luna` | low | `20260710T080607Z-d15bf2ca` | complete | 2200/2900 | 22 | 7 | 0 | 16m 10s |
| Codex CLI | `gpt-5.6-luna` | medium | `20260710T082225Z-8be54afa` | complete | 2000/2900 | 20 | 9 | 0 | 19m 51s |
| Codex CLI | `gpt-5.6-luna` | high | `20260710T084224Z-5fdc40c6` | complete | 2100/2900 | 21 | 8 | 0 | 27m 18s |
| Codex CLI | `gpt-5.6-luna` | xhigh | `20260709T175826Z-b8e5f041` | complete | 1900/2900 | 19 | 10 | 0 | 23m 47s |
| Codex CLI | `gpt-5.6-luna` | max | `20260710T152845Z-c0067294` | complete | 2200/2900 | 22 | 7 | 0 | 40m 20s |
| Codex CLI | `gpt-5.5` | low | `20260625T072711Z-e484ea0f` | complete | 2100/2600 | 21 | 5 | 0 | 19m 25s |
| Codex CLI | `gpt-5.5` | medium | `20260625T073226Z-3fce189c` | complete | 1900/2600 | 19 | 7 | 0 | 22m 15s |
| Codex CLI | `gpt-5.5` | high | `20260625T073227Z-167ae812` | complete | 1900/2600 | 19 | 7 | 0 | 25m 59s |
| Codex CLI | `gpt-5.5` | xhigh | `20260624T182835Z-4ad8b555` (+2) | complete | 2200/2600 | 22 | 4 | 0 | 41m 03s |
| Codex CLI | `gpt-5.4` | low | `20260625T073231Z-84de082a` | complete | 2000/2600 | 20 | 6 | 0 | 17m 45s |
| Codex CLI | `gpt-5.4` | medium | `20260625T073227Z-76c2964d` | complete | 2100/2600 | 21 | 5 | 0 | 20m 55s |
| Codex CLI | `gpt-5.4` | high | `20260625T073228Z-a5a4a383` | complete | 2200/2600 | 22 | 4 | 0 | 28m 16s |
| Codex CLI | `gpt-5.4` | xhigh | `20260624T190640Z-fa04a19c` (+2) | complete | 2100/2600 | 21 | 5 | 0 | 40m 02s |
| Codex CLI | `gpt-5.4-mini` | low | `20260627T154139Z-a762c204` | complete | 2100/2600 | 21 | 5 | 0 | 13m 51s |
| Codex CLI | `gpt-5.4-mini` | medium | `20260627T154149Z-11277553` | complete | 2100/2600 | 21 | 5 | 0 | 17m 59s |
| Codex CLI | `gpt-5.4-mini` | high | `20260627T154205Z-4e04ba57` | complete | 2100/2600 | 21 | 5 | 1 | 29m 05s |
| Codex CLI | `gpt-5.4-mini` | xhigh | `20260624T194359Z-268b0abe` (+2) | complete | 1900/2600 | 19 | 7 | 3 | 39m 46s |
| Claude Code | `claude-opus-4-8` | low | `20260627T214634Z-4e66a550` | complete | 1900/2600 | 19 | 7 | 0 | 9m 02s |
| Claude Code | `claude-opus-4-8` | high | `20260628T071803Z-ca820a9b` | complete | 2100/2600 | 21 | 5 | 0 | 12m 58s |
| Claude Code | `claude-opus-4-8` | xhigh | `20260628T154937Z-ed26a81d` | complete | 2100/2600 | 21 | 5 | 0 | 22m 03s |

All runs used a 240 second per-task agent timeout and the same task prompt contract: read `NIXBENCH_PROMPT.md`, edit only the copied task workdir, do not inspect hidden evaluators, run local checks if useful, then stop.

## Effort Sweep Notes

| Model | Notes |
|---|---|
| `gpt-5.5` | Low effort recorded 21/26, medium and high recorded 19/26, and the xhigh baseline recorded 22/26. |
| `gpt-5.4` | Scores increased from 20/26 at low effort to 21/26 at medium and 22/26 at high, while xhigh recorded 21/26. |
| `gpt-5.4-mini` | Low, medium, and high effort each recorded 21/26; the xhigh baseline recorded 19/26 with three timeouts. |
| `claude-opus-4-8` | Explicit low, high, and xhigh efforts recorded 19/26, 21/26, and 21/26. |
| `gpt-5.6-sol` | Low and xhigh passed 21/29. Medium, high, and max passed 22/29; max took 47m 54s and timed out twice. Ultra remains paused. |
| `gpt-5.6-terra` | Low passed 20/29, medium and high passed 21/29, and xhigh passed 19/29. Max and ultra remain paused. |
| `gpt-5.6-luna` | Low and max passed 22/29, medium passed 20/29, high passed 21/29, and xhigh passed 19/29. Low was the fastest GPT-5.6 row at 16m 10s. |
| Highest historical pass rate | `gpt-5.4` high and `gpt-5.5` xhigh both passed 22/26 tasks (85%); `gpt-5.4` high used less agent time. |

## Baseline Per-Task Results

This table shows the xhigh/default baseline columns used by the detailed results page.

The Codex columns use the original xhigh baselines. The Claude column preserves the original default composite from `20260624T202141Z-881ef1e9` plus the two supplemental task artifacts; it is distinct from the later explicit Claude xhigh run.

| Task | GPT-5.5 xhigh | GPT-5.4 xhigh | GPT-5.4 mini xhigh | Claude Opus 4.8 |
|---|---:|---:|---:|---:|
| `container-native-vs-oci` | FAIL | FAIL | FAIL | FAIL |
| `debug-infinite-recursion` | PASS | PASS | PASS | PASS |
| `debug-network-false-lead` | FAIL | FAIL | FAIL | FAIL |
| `devshell-tooling-contract` | PASS | PASS | PASS | PASS |
| `fetcher-source-pin` | PASS | PASS | PASS | PASS |
| `fhs-binary-wrapper` | PASS | PASS | PASS | PASS |
| `flake-input-package-selection` | PASS | PASS | PASS | PASS |
| `flake-per-system-outputs` | PASS | PASS | FAIL | PASS |
| `home-manager-extra-special-args` | PASS | PASS | PASS | PASS |
| `home-manager-wsl-module-import` | PASS | PASS | PASS | PASS |
| `home-manager-xdg-files` | PASS | PASS | PASS | PASS |
| `issue-report-quality` | FAIL | FAIL | FAIL | FAIL |
| `lang-attrsets-normalize` | PASS | PASS | PASS | PASS |
| `module-path-composition` | PASS | PASS | PASS | PASS |
| `module-service-options` | FAIL | PASS | PASS | PASS |
| `module-stale-option-migration` | PASS | PASS | PASS | PASS |
| `module-system-boundaries` | PASS | PASS | PASS | PASS |
| `mutable-config-home-manager` | PASS | PASS | PASS | PASS |
| `overlay-module-boundary` | PASS | PASS | PASS | PASS |
| `overlay-override-package` | PASS | PASS | PASS | PASS |
| `package-name-lookup-contract` | PASS | PASS | PASS | PASS |
| `package-python-application` | PASS | FAIL | FAIL | PASS |
| `package-stdenv-cli` | PASS | FAIL | FAIL | FAIL |
| `purity-wrapper-derivation` | PASS | PASS | PASS | PASS |
| `python-cuda-uv2nix-patch` | PASS | PASS | PASS | PASS |
| `string-escaping-systemd` | PASS | PASS | FAIL | FAIL |

## Outcome Notes

| Task | Notes |
|---|---|
| `container-native-vs-oci` | The xhigh/default baseline rows did not pass this task, while GPT-5.5 low passed it during the effort sweep. |
| `debug-network-false-lead` | No recorded row in this set passed this task; GPT-5.4 mini xhigh timed out. |
| `issue-report-quality` | No recorded row in this set passed this task. |
| `package-stdenv-cli` | Only GPT-5.5 xhigh passed this task among the GPT effort rows. |

## Commands

Effort sweep Codex runs used this shape, with `<model>` set to `gpt-5.5` or `gpt-5.4` and `<effort>` set to `low`, `medium`, or `high`:

```sh
python3 -u bench.py run-all --agent-timeout-seconds 240 --agent-cmd 'codex -c model_reasoning_effort=<effort> --ask-for-approval never exec -m <model> --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

The original xhigh/default comparison commands did not pass `-c model_reasoning_effort=...`; the local Codex config was set to `model_reasoning_effort = "xhigh"` for the Codex baseline runs.

The June 27 `gpt-5.4-mini` effort runs used the same command shape with `<model>` set to `gpt-5.4-mini`.

The Claude Opus effort runs used the same Claude Code command shape with `--model opus` and `--effort low`, `--effort high`, or `--effort xhigh`.

The July 9 GPT-5.6 runs used the compatible Codex binary bundled with the desktop app because the separately installed Codex CLI 0.143.0 rejected these models as requiring a newer version. Each run used the same prompt contract and timeout shown above, with `<model>` set to `gpt-5.6-sol`, `gpt-5.6-terra`, or `gpt-5.6-luna`, and explicit `model_reasoning_effort="xhigh"`.

The July 10 GPT-5.6 effort rows used that same bundled binary and command shape with explicit low, medium, high, or max effort. The first attempt reached the account usage limit after eight complete rows; quota-contaminated partial directories were discarded and the affected rows were rerun from task 1 after reset. Every recorded summary above is a complete, quota-clean 29-task run.
