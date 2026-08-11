# 2026-08-08 through 2026-08-10 Local OpenCode Model Runs

These two single-trial NixBench runs measured local quantized models through OpenCode and llama.cpp against the 29-task corpus. They are recorded as `default` effort because OpenCode did not expose a reasoning-effort control comparable to the Codex effort sweep. Both llama.cpp servers used a 2,048-token reasoning budget.

The raw `results/` artifacts are intentionally not tracked because they contain logs, diffs, and machine-local paths. The checked site dataset retains each run ID, score, elapsed agent time, timeout count, host, platform, and repository revision.

## Summary

| Agent | Model | Run ID | Score | Passed | Failed | Timeouts | Agent time |
|---|---|---|---:|---:|---:|---:|---:|
| OpenCode + llama.cpp | Gemma 4 26B-A4B IT QAT Q4_0 | `20260808T200851Z-8bab6819` | 1000/2900 | 10 | 19 | 3 | 15h 03m 24s |
| OpenCode + llama.cpp | Ternary Bonsai 27B Q2_0 | `20260809T111308Z-25eea85d` | 700/2900 | 7 | 22 | 4 | 19h 58m 03s |

Each row is one observation, so neither has a confidence interval. The website renders them as hollow single-run marks rather than replicated configuration means.

## Runtime

- Host: `kim`
- CPU: AMD Ryzen AI 9 HX 370, 24 logical CPUs
- Memory: 58 GiB available to the operating system
- GPU: integrated Radeon 890M through Vulkan
- Agent: OpenCode 1.18.13
- Inference runtime: llama.cpp build 9599 (`9ca265a57`)
- Context: 32,768 tokens, one inference slot
- Reasoning budget: 2,048 tokens
- Agent timeout: 3,600 seconds per task
- Network state: unknown
- Gemma model: `gemma-4-26B_q4_0-it.gguf`, CPU inference
- Bonsai model: `Ternary-Bonsai-27B-Q2_0.gguf`, Vulkan offload

The runs executed sequentially. To keep the unattended host below its thermal cutoff, the active benchmark was ultimately limited to a 500% cgroup CPU quota and guarded by a monitor that stopped both benchmark sessions after three consecutive 95°C readings. Bonsai used six llama.cpp CPU threads pinned to CPUs 4–9 for its complete recorded run.

Gemma's resource profile changed during its run: it began with the default 12 llama.cpp CPU threads, briefly overlapped an abandoned partial Bonsai run, and was later moved to the sequential 500% quota. Scores remain valid task outcomes, but Gemma timing and timeout counts are not controlled performance measurements. Bonsai was restarted from task one after the sequential and thermal limits were established; its timing is internally consistent but still reflects the safety cap.

The two repository revisions shown on the leaderboard are comparable for this corpus: `git diff 6c4205b2e2cf931545fbd2eebda50bc7a8363dbb 20e70fd435dfb53d90f36595f27701939bf49a2c -- tasks/` is empty.

## Passed Tasks

Gemma passed:

- `debug-infinite-recursion`
- `flake-input-package-selection`
- `home-manager-extra-special-args`
- `home-manager-wsl-module-import`
- `module-path-composition`
- `module-stale-option-migration`
- `module-system-boundaries`
- `overlay-module-boundary`
- `package-name-lookup-contract`
- `purity-wrapper-derivation`

Bonsai passed:

- `flake-input-package-selection`
- `home-manager-extra-special-args`
- `home-manager-wsl-module-import`
- `module-stale-option-migration`
- `overlay-module-boundary`
- `package-name-lookup-contract`
- `python-cuda-uv2nix-patch`

## Timeouts

Gemma timed out on `flake-per-system-outputs`, `lang-attrsets-normalize`, and `package-python-application`.

Bonsai timed out on `debug-infinite-recursion`, `flake-per-system-outputs`, `lang-attrsets-normalize`, and `module-service-options`.
