# 2026-09-10 Astra via isolated Pi

This run compared GPT-6 Astra at low, medium, high, and extra-high reasoning through Pi and CLIProxyAPI. Four Herdr panes ran the configurations concurrently. Every task started with a fresh Pi home, no skills, and an isolated filesystem.

Three full 29-task trials completed without model transport errors. Extra-high lost router access on its final two tasks and is excluded from the leaderboard. These are single observations, not replicated estimates.

## Results

| Effort | Passed | Score | Pass rate | Agent time | Timeouts | Status |
|---|---:|---:|---:|---:|---:|---|
| Low | 22/29 | 2200/2900 | 75.9% | 14m 21s | 0 | Complete |
| Medium | 23/29 | 2300/2900 | 79.3% | 14m 55s | 0 | Complete |
| High | 22/29 | 2200/2900 | 75.9% | 17m 48s | 0 | Complete |
| Extra-high | 22/27 evaluated model attempts | Not comparable | Not comparable | 21m 13s | 0 | Two tasks blocked by router errors |

Agent time is the sum of task process durations, including startup and retries. Extra-high's total includes the two failed transport attempts. The four runs started between 09:00:27 and 09:00:54 UTC; the last process finished at 09:22:08 UTC.

Medium passed one more task than low or high. High took 24% more agent time than low without improving its total score. One trial per configuration cannot establish a stable ranking or a confidence interval. Concurrent requests shared a router and host, so timing also reflects contention and provider conditions.

## Run identity

| Effort | Run ID | Herdr pane |
|---|---|---|
| Low | `20260910T090027Z-79e6aa0c` | `wC:p2` |
| Medium | `20260910T090054Z-25467b2c` | `wC:p4` |
| High | `20260910T090054Z-2b287c72` | `wC:p3` |
| Extra-high | `20260910T090054Z-09486029` | `wC:p5` |

- Model selection: `cliproxyapi/gpt-6-astra`, using the OpenAI Responses API.
- Agent: Pi 0.85.1, stock tools and system prompt.
- Reasoning levels: explicit `low`, `medium`, `high`, and `xhigh` mappings. No `max` run was requested.
- Context window: 272,000 tokens. Maximum output: 128,000 tokens.
- Host: `kim`, `x86_64-linux`, Linux 6.18.45, glibc 2.42.
- Nix: 2.34.8. Bubblewrap: 0.11.2.
- Per-task agent timeout: 240 seconds for every configuration.
- Corpus revision: `c65e9729db6b93895519f3d3a79760c711a91ac3`. No task files or evaluators changed.
- The local CLI gained `--kind pi` metadata support before launch. Website changes do not affect task evaluation.

The recorded model ID identifies the requested router alias. It is not an independent attestation of the upstream model or account selected by CLIProxyAPI.

## Isolation

For each task, the launcher created a new temporary home and a new `.pi/agent` directory. It wrote only a minimal `models.json` defining the CLIProxyAPI connection and Astra's reasoning map. It copied no user settings, authentication store, extensions, skills, context files, templates, or session history. The router handled upstream authentication outside the sandbox.

Pi ran with:

```sh
pi --no-extensions --no-skills --no-prompt-templates \
  --no-themes --no-context-files --no-session --no-approve \
  --provider cliproxyapi --model gpt-6-astra \
  --thinking "$effort" --mode json --print "$prompt"
```

Bubblewrap used `--unshare-all --share-net --die-with-parent`. The sandbox exposed:

- The copied task workspace, writable at `/workspace`.
- A fresh writable home at `/home/agent` and private `/tmp`.
- Read-only `/nix/store` and the system command profile.
- A private process namespace, device setup, resolver files, and TLS certificates.

The benchmark repository, hidden tests, reference solutions, results, original home directory, and host Nix daemon socket were not mounted. Nix could evaluate local expressions using its private fallback store. The environment was cleared and rebuilt with only the command path, home, locale, Pi configuration, certificates, and Nix settings. Startup networking and telemetry were disabled with `PI_OFFLINE=1` and `PI_TELEMETRY=0`.

Network access remained enabled to reach CLIProxyAPI at `127.0.0.1:8317`. This is filesystem and process isolation, not a network-isolated VM: the sandbox shared the host network and could read the installed Nix store.

Preflight checks verified that the original home was absent, the Pi directory initially contained only one configuration file, and `nix-instantiate --eval --expr '1 + 1'` returned `2`. A model smoke test reported `PI_PROVIDER=cliproxyapi`, `PI_MODEL=gpt-6-astra`, and `PI_REASONING_LEVEL=low` from inside the sandbox and completed successfully. An earlier, mistaken direct OpenAI Codex preflight failed authentication before any benchmark trials began; it contributed no scores.

The task prompt was identical across configurations:

```text
You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop.
```

## Extra-high router failure

Extra-high completed 27 model attempts, passing 22 and failing five hidden checks. On `string-escaping-systemd` and `xdg-portal-merge`, CLIProxyAPI returned HTTP 503 errors, including:

```text
auth_unavailable: no auth available (providers=codex, model=gpt-6-astra)
```

Each affected task logged four failed assistant responses, including Pi's automatic retries. Neither task produced a diff. Pi nevertheless returned exit code zero, so the generic benchmark runner evaluated the untouched starters and reported a nominal 2200/2900 complete trial. That nominal result is not a valid full-corpus model score.

The raw result files remain unchanged. The extra-high study metadata has `publish: false` and an exclusion reason, and its trial is absent from the checked website dataset. No replacement tasks, composite score, or selective retry results were substituted. A valid extra-high comparison still needs a fresh full-corpus trial after router access is restored.

## Failure pattern and evaluator caveats

All three complete trials failed these six tasks:

- `container-native-vs-oci`
- `debug-network-false-lead`
- `devshell-tooling-contract`
- `purity-wrapper-derivation`
- `rust-no-network-build`
- `string-escaping-systemd`

Low additionally failed `package-python-application`. High additionally failed `package-stdenv-cli`. Extra-high's five evaluator failures were the first five tasks in the common-failure list above; its final two tasks were infrastructure failures instead.

Some failures depend on restrictions in the evaluator rather than proving that the model misunderstood Nix:

- The container evaluator imports the module directly and reads `module.config`. The candidates use NixOS's top-level option shorthand, so the check fails with `attribute 'config' missing` before examining the native container settings. The public prompt does not require an explicit outer `config` attribute.
- The network prompt describes observations without defining their field schema. The evaluator uses nested fields such as `ipv4.hasAddress`, `arp.gateway`, and `dns.lookup`. Candidates infer different field names and return `unknown` for the hidden input. This confounds diagnosis quality with guessing an undocumented schema.
- The devshell evaluator requires a particular single-line assignment pattern. Low's candidate uses a multiline `NIX_CONFIG` assignment with `extra-experimental-features`; the regular expression rejects it. The official score is unchanged, and the run does not establish that this shell hook is behaviorally wrong.
- The purity-wrapper check expects the literal substring `makeWrapper /nix/store/.../bin/bash`. Low's candidate quotes that argument, causing the regular-expression assertion to fail.
- Low uses Python's `dependencies` attribute, while the fake builder checks `propagatedBuildInputs`. The failure is an attribute-contract mismatch in the evaluator.
- The Rust task uses a constrained fake library. Low's candidate calls `lib.getLib`, which that library does not provide.

These notes do not rescore the benchmark. Reference validation passed all 29 tasks, and starter validation rejected all 29, but those smoke checks do not establish that every valid alternative implementation is accepted.

## Artifacts and checked data

Raw artifacts are retained locally under `results/astra-pi-20260909/`. The directory name reflects the setup date; the actual corpus trials ran on September 10. It contains each run's `agent.log`, `check.log`, `diff.patch`, `result.json`, and `summary.json`, plus study summaries, preflight events, validation logs, pane IDs, and the exact launch scripts.

Launch script hashes:

- `sandbox.py`: `8e36c22dbad4a47c87864c42a992657b6ff16e65be5ed5c7cb6710fe58818406`
- `run-effort.sh`: `da73fbb2eae80bfb06b298fa1bfba5a52b342af22381ec844efbce3eff767bad`

The three valid trials are recorded in `site/src/data/benchmark-trials.json` under the separate `gpt6AstraPi` series with agent kind `pi`. Existing benchmark rows are preserved. Import command, after excluding the incomplete extra-high study:

```sh
python3 bench.py --results-dir results/astra-pi-20260909 export-site \
  --task-count 29 --minimum-trials 1 --expected-configurations 3 \
  --merge-existing --output site/src/data/benchmark-trials.json
```

Raw results remain untracked, following the repository's existing artifact policy. Nothing was pushed or deployed.
