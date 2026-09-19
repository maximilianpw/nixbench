# Reproducibility

NixBench is built to make benchmark runs inspectable, but full reproducibility still depends on the agent, model, machine, and task corpus version.

## What The Harness Records

For each task, the harness records:

- Agent command.
- Agent return code.
- Agent timeout status.
- Agent duration.
- Evaluator command.
- Evaluator return code.
- Evaluator timeout status.
- Evaluator duration.
- Diff from starter to final workdir.
- Structured result JSON.

The aggregate run writes `results/<run-id>/summary.json`. Repeated runs
checkpoint `results/studies/<study-id>/summary.json` after every attempt. Valid
complete attempts enter `trials` and estimates. Invalid or incomplete attempts
remain in the `attempts` ledger with exclusion reasons and no score
denominator. Non-timeout agent process errors stop a study after that
checkpoint.

New study summaries use schema version 3. Each valid trial contains the
task-by-trial observation matrix, and each attempt retains its task records as
the exclusion population. The matrix's task and rubric evidence is primitive;
`normalized_score`, pass/fail lists, failure classes, and all trial totals are
redundant fields recomputed and cross-checked by the shared validator before
current reporting or publication. Use the canonical report command to inspect
a study:

```sh
python3 bench.py report-study \
  --study-path results/studies/<study-id>/summary.json \
  --json
```

If an older study still references readable run summaries, the loader hydrates
its observations from those files. Otherwise, it marks the study
`aggregate_only = true` and omits task-level claims.

Each new run records a content-addressed corpus digest and configuration ID. The corpus digest covers the manifest, task metadata, prompts, starters, references, evaluators, and contract fixtures. The Git revision remains provenance and does not identify benchmark content. Site-only or documentation-only commits therefore do not change the corpus digest.

The configuration ID covers the controlled run protocol and corpus digest. This includes the model ID and identity evidence, harness version, effort, network and tool policy, isolation profile, system, timeout, wrapper-prompt SHA-256, agent-command SHA-256, and the registered adapter bundle digest. Display fields such as `series`, `marker`, and `label` do not affect it. Host and platform are excluded from correctness identity and produce a separate timing environment ID. Compare timings only when that ID matches.

Schema-3 metadata retains the exact non-secret hash input in the versioned
`controlled_protocol` payload. The raw wrapper prompt and agent command are not
copied there; their SHA-256 values are the controlled inputs. The shared
protocol function recomputes `configuration_id` from `corpus_digest` and this
payload, and validation also checks the flattened compatibility fields against
it. A self-asserted or stale `configuration_id` is therefore rejected.

## Recommended run metadata

When publishing or comparing results, record:

- NixBench Git commit as provenance.
- Agent command hash and wrapper-prompt hash. Keep raw commands in private run artifacts when they contain sensitive arguments.
- Agent version.
- Model ID and model identity evidence. A router alias may be explicitly recorded as unverified.
- Timeout.
- Host OS and architecture.
- Whether network access was available.
- Whether Nix was configured with flakes enabled.

Use `python3 bench.py corpus-id --json` to inspect the current corpus identity. Calibration drafts consume only strict schema-3 studies for that exact identity:

```sh
python3 bench.py calibration-report \
  --studies-dir results/studies \
  --output /tmp/nixbench-calibration.json
```

The command writes only to the explicit output path. It deduplicates
configuration/run/task cells, retains invalid and incomplete attempts, reports
unavailable discrimination without inventing a value, and never approves a
record or changes `corpus/task-lifecycle.toml`. A changed task or corpus digest
makes prior records stale. Maintainers manually review the draft before copying
approved records into the checked registry.

Use a reviewed protocol file for publishable runs:

```sh
python3 bench.py run-all \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd 'your-agent-command'
```

Runs without `--protocol-file` remain available for local compatibility, but they set `protocol_complete = false`. `export-site` rejects them unless the operator supplies `--allow-legacy-protocol`.

Current-protocol website exports must also name the checked corpus release.
The schema-3 release manifest distinguishes all release-controlled tasks from
the active task set and records activation eligibility. A structurally healthy
`calibrating` release has no publishable active task set; export and publication
checks fail closed until reviewed current-digest calibration activates it.


```sh
python3 bench.py --results-dir results export-site \
  --release-manifest corpus/releases/2.0.0.json \
  --output site/src/data/benchmark-trials.json
```

`export-site` does not maintain a weaker parallel validation path. Before it
groups studies or computes site reports, it runs the shared schema-3 validator
that recomputes primitive evidence and controlled protocol identity, then runs
the canonical publication check against the supplied release manifest. A
failure leaves the destination unchanged. Explicit legacy imports may omit the
manifest, remain labelled with their historical protocol and scoring schema,
and do not satisfy expected current-configuration counts.

A complete protocol sets `completion_attestation = "required"`, names a
registered adapter such as `agent_adapter = "codex-json"`, and selects that
adapter with `--agent-adapter`. The harness retains the legacy entry-point
executable digest and separately derives a canonical adapter bundle digest.
The bundle digest uses stable repository-relative names, file lengths and
bytes, and executable-bit state. It snapshots and removes the adapter's status
file before the evaluator runs. The bundled Codex adapter consumes
`codex exec --json`
events and removes all harness-private paths from the Codex child environment.
It does not infer success from human-readable log text. A raw `--agent-cmd`
without a registered adapter remains protocol-incomplete.

The `codex-json` bundle contains only `scripts/codex-agent-adapter.py`; its
trust level is `provisional-same-uid`. Local same-UID processes are outside its
sealing guarantee. The `codex-json-bwrap` bundle contains
`scripts/bwrap-codex-agent.py`, `nixbench/isolation.py`, and
`launchers/linux-bwrap-v1.toml`. Private held-out publication uses that adapter
with `isolation_profile = "linux-bwrap-v1"`.
Its trusted outer process writes status evidence while the model runs in a
bubblewrap namespace without the repository, corpus, evaluator, reference,
results, host home, or Nix daemon socket. `publication-check` rejects held-out
studies without a successful approved preflight or when the study, registered
adapter, and schema-3 release manifest do not carry the same bundle digest.
Older release manifests are not silently upgraded. Publication first validates
the schema-3 release manifest, then requires corpus ID, version,
digest, visibility, and task count to agree. For a public corpus, every
observation `task_digest` and the exact task-ID set must match the manifest's
`task_digests` and `active_tasks`. For a private held-out corpus, the validator
hashes each retained observation digest and compares the resulting set with the
manifest's opaque active-task hashes; task IDs are not emitted in public output.
Altered task digests, protocol identity, normalized scores, or redundant trial
totals make the study ineligible.

Adapter bundle identity covers the repository-local harness code and policy
that constructs and checks isolation. It does not identify the model provider,
remote provider code, model weights, or the external Codex/model executable.

Current studies use the adapter through `scripts/run-current-studies.sh`.
Generic `--agent-cmd` commands remain useful for local runs, but they are
unattested and not publishable under a complete protocol.

## Determinism boundaries

The bundled tasks are mostly deterministic because evaluators use local Nix evaluation and fake builders. Agent behavior is not deterministic unless the agent and model expose a reliable deterministic mode.

For serious comparisons, use `run-all --trials 5` or more and report:

- raw earned and available points;
- macro task score, macro pass rate, and point-weighted score;
- trial, task, and valid-observation counts;
- observed ranges and sample standard deviations;
- timeout, invalid-measurement, and incomplete-attempt rates;
- exclusion reasons and common failure classes;
- method name, method version, sampling unit, warnings, and interval bounds.

The Student's t interval describes variation across independent repetitions of
the same fixed corpus under the same configuration. It assumes approximate
normality of the trial statistic. It is not a future-run prediction interval,
an evaluator-correctness interval, a claim about all Nix work, evidence of
model identity, or a significance test between configurations.

Task/run resampling describes sensitivity to the observed corpus composition.
It does not provide a population-generalization claim because NixBench has no
defined random sampling frame for all Nix work. The report omits this interval
for incomplete task-by-trial matrices or groups with fewer than five tasks.

Compare duration intervals only within one timing environment ID. When a
correctness configuration spans multiple timing environments, the canonical
report keeps separate duration groups and refuses to calculate a combined
timing interval.

## Versioning the corpus

Changing task metadata, a prompt, starter, reference, evaluator, rubric, or contract fixture changes the digest. Treat semantic corpus changes as benchmark-version changes, even though Git state itself has no effect on the digest.

Suggested policy:

- Patch version: docs or harness-only changes.
- Minor version: new tasks added, no existing tasks changed.
- Major version: existing task behavior or scoring changed.

## Avoiding leakage

The hidden evaluator is intentionally outside the copied workdir. Do not give the agent paths to `tasks/<id>/tests/check.sh`. Do not include hidden assertions in `prompt.md`.

For public leaderboards, use a private held-out corpus in addition to the
public development corpus. The active private corpus stays outside this
repository. See [benchmark-governance.md](benchmark-governance.md) for its
release, redaction, calibration, and rotation rules.
