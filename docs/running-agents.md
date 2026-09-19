# Running agents

NixBench accepts any agent that can be invoked as a shell command. Generic
commands are suitable for local runs. Publishable protocols also require a
trusted completion adapter.

The harness copies a task starter into a temporary directory and runs the agent command with that temporary directory as the current working directory. The agent should read `NIXBENCH_PROMPT.md`, edit local files, and exit.

The agent environment includes `NIXBENCH_TASK_ID`, `NIXBENCH_WORKDIR`, and
`NIXBENCH_PROMPT`. It does not include the original task directory, hidden
evaluator path, reference solution path, or score file path. When a complete
protocol requires attestation, only the registered adapter receives
`NIXBENCH_AGENT_STATUS_FILE`. It removes that path and every other
harness-private path from the model-controlled child environment.

## Generic Pattern

```sh
python3 bench.py run-all \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd 'your-agent-command'
```

For one task:

```sh
python3 bench.py run package-stdenv-cli \
  --agent-timeout-seconds 240 \
  --agent-cmd 'your-agent-command'
```

`protocols/example.toml` is a template. Copy it and set its system, timeout,
model, harness, effort, network, isolation, tool policy, and registered adapter
to the values used by the run. The timeout, system, and adapter must match the
command-line values. The harness hashes the wrapper and agent command. For a
registered adapter it records both the legacy entry-point executable digest and
a canonical digest of the adapter's declared local trust bundle. It stores the
hashes, not the raw command, in publication metadata.

## Repeated studies

A publishable comparison should repeat the entire corpus. `--trials` writes every trial as a normal run and also writes a study summary containing the mean, observed range, standard deviation, and Student's t 95% confidence interval:

```sh
python3 bench.py run-all \
  --trials 5 \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --model gpt-5.6-sol \
  --series gpt56Sol \
  --effort high \
  --kind codex \
  --marker SH \
  --label "GPT-5.6 Sol via Codex CLI" \
  --agent-version "$(codex --version)" \
  --network unknown \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd 'your-agent-command'
```

Each attempt remains available at `results/<run-id>/summary.json`. The combined
study is checkpointed after every attempt at
`results/studies/<study-id>/summary.json`, so a later infrastructure or quota
failure does not discard earlier evidence. Only complete, valid attempts enter
the `trials` list and estimates. A single trial intentionally has no confidence
interval because one observation cannot estimate uncertainty.

For a resumable configuration matrix, query completed evidence with the same protocol, wrapper, command, timeout, and corpus before scheduling another trial:

```sh
python3 bench.py --results-dir results study-count \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd 'your-agent-command'
```

[`scripts/run-current-studies.sh`](../scripts/run-current-studies.sh) uses this checkpoint to visit each current model/effort configuration once per round and resume until every configuration reaches the requested trial count.

To produce the checked JSON consumed by the website after running one or more fully labelled studies:

```sh
python3 bench.py --results-dir results export-site \
  --release-manifest corpus/releases/2.0.0.json \
  --task-count 29 \
  --minimum-trials 5 \
  --expected-configurations 14 \
  --merge-existing \
  --output site/src/data/benchmark-trials.json
```

`export-site` is a presentation transform over checked publication evidence,
not an independent validator. Whenever any selected study uses the current
protocol, `--release-manifest` is mandatory. The exporter invokes the canonical
schema-3 current-study validator and `publication-check` policy before grouping
or reporting any study. It fails without modifying the output when the release,
corpus task matrix, primitive observations, controlled protocol identity,
completion evidence, or publication policy does not match. It also retains the
site-specific minimum-trial and expected-current-configuration gates. Zero-trial
attempt ledgers are skipped so an infrastructure failure does not hide valid
sibling studies or block resumption. Private-heldout and retired studies remain
ineligible for direct public-site export. Historical studies require the
explicit `--allow-legacy-protocol` compatibility flag and never count toward
`--expected-configurations`.

When the local results archive contains only newly collected studies, merge those checked rows into the existing site dataset instead of replacing prior evidence:

```sh
python3 bench.py --results-dir results export-site \
  --release-manifest corpus/releases/2.0.0.json \
  --task-count 29 \
  --minimum-trials 1 \
  --expected-configurations 2 \
  --merge-existing \
  --output site/src/data/benchmark-trials.json
```

The trial and configuration gates apply to the studies being imported; `--merge-existing` then replaces matching row IDs and preserves unrelated checked rows. Keep the original run and study summaries in the results archive so an imported row remains independently auditable.

## Codex

Example:

```sh
python3 bench.py run-all \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd 'codex exec --json --ephemeral --skip-git-repo-check --sandbox workspace-write'
```

Notes:

- `--ephemeral` avoids persistent session noise.
- `--skip-git-repo-check` is useful because task workdirs are temporary copies.
- `--sandbox workspace-write` allows editing local starter files.
- `--json` provides native events for the trusted adapter. The adapter records
  `thread.started`, `turn.completed`, native error events, and the launcher exit
  code. It does not search logs for success phrases.

## Agent prompt contract

Good benchmark prompts for agents should include:

- Read `NIXBENCH_PROMPT.md`.
- Modify only files in the current directory.
- Do not inspect hidden evaluator files.
- Run local checks if useful.
- Exit when done.

Avoid telling the agent the hidden test path.

## Timeouts

The agent timeout is controlled separately from task evaluator timeout:

```sh
python3 bench.py run-all \
  --protocol-file protocols/example.toml \
  --wrapper-prompt-file protocols/agent-wrapper.txt \
  --agent-timeout-seconds 240 \
  --agent-adapter codex-json \
  --agent-cmd '...'
```

Task evaluator timeouts are set in each task's `metadata.toml`:

```toml
timeout_seconds = 60
```

After each agent or evaluator command finishes, the harness terminates any remaining processes in that command's process group; it does the same immediately when a timeout expires. This prevents ordinary background children from continuing into the evaluator or later tasks. Commands that deliberately detach into a separate session still require external sandboxing; the harness is not a container or VM boundary.

## Held-out isolation

Public development runs may use the provisional `codex-json` adapter. A
private held-out publication must use a protocol with:

```toml
isolation_profile = "linux-bwrap-v1"
agent_adapter = "codex-json-bwrap"
network_policy = "disabled" # or "enabled", when the protocol requires it
```

Select the same adapter on the command line. The trusted launcher constructs
the bubblewrap process itself. A raw command cannot claim this profile. The
launcher mounts only the copied workspace read-write, creates a fresh home and
`/tmp`, mounts required system paths read-only, and omits the repository,
corpus, evaluator, reference, results, host home, and Nix daemon socket.

The trusted `codex-json-bwrap` bundle is exactly:

- `scripts/bwrap-codex-agent.py`, the outer launcher and attestation owner;
- `nixbench/isolation.py`, which constructs the namespace and preflight; and
- `launchers/linux-bwrap-v1.toml`, which declares the reviewed policy.

Changing any member changes the adapter bundle digest and therefore the
configuration identity. Held-out publication requires the study metadata,
current adapter registration, and schema-2 release manifest to agree on that
digest. The bundle does not cover provider-controlled remote code, model
weights, or the external Codex/model executable.

Before starting Codex, a generic in-namespace preflight checks that the Nix
daemon socket is absent and `/workspace` is writable. The launcher uses a
fixed PATH and does not put forbidden host paths in the model process's
arguments or environment. The cleared inner command runs as PID 1 so the
outer environment is not visible through `/proc/1/environ`. The outer
launcher owns the attestation path and records the preflight and Codex JSON
completion state. After Codex exits, the
runner rejects workspace symlinks that resolve outside `/workspace` before it
runs the evaluator. `publication-check` rejects the study if this evidence is
missing or failed.

Held-out workspaces use `/tmp/nixbench-isolated-<random>/work` on the host.
The staging path contains no task, corpus, run, model, or configuration
identity. The preflight verifies that neutral source shape against
`/proc/self/mountinfo` before starting the model command. An agent executable
outside the workspace is copied to
`/tmp/nixbench-isolated-agent-<random>/agent` before its read-only bind, so its
original host path is not exposed either.

## Keeping workdirs

Use `--keep-workdir` when debugging a run:

```sh
python3 bench.py run lang-attrsets-normalize \
  --keep-workdir \
  --agent-cmd '...'
```

The resulting `result.json` will include the workdir path. Without `--keep-workdir`, temporary task workdirs are removed after evaluation.

## Reading results

The fastest way to inspect a run:

```sh
python3 - <<'PY'
import json
from pathlib import Path

summary = json.loads(Path("results/<run-id>/summary.json").read_text())
print(f"{summary['passed']}/{summary['passed'] + summary['failed']} passed")
for task in summary["tasks"]:
    print(task["task_id"], task["passed"], task["score"])
PY
```

Then inspect failed tasks:

```sh
sed -n '1,160p' results/<run-id>/<task-id>/check.log
sed -n '1,220p' results/<run-id>/<task-id>/diff.patch
```
