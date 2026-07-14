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

The aggregate run writes `results/<run-id>/summary.json`. Repeated runs additionally checkpoint `results/studies/<study-id>/summary.json` after every valid trial, including per-trial outcomes and 95% Student's t intervals for tasks passed, score rate, total agent time, and seconds per task. Non-timeout agent process errors stop a study instead of becoming benchmark failures.

## Recommended Run Metadata

When publishing or comparing results, record:

- NixBench git commit.
- Agent command.
- Agent version.
- Model name.
- Timeout.
- Host OS and architecture.
- Whether network access was available.
- Whether Nix was configured with flakes enabled.

## Determinism Boundaries

The bundled tasks are mostly deterministic because evaluators use local Nix evaluation and fake builders. Agent behavior is not deterministic unless the agent and model expose a reliable deterministic mode.

For serious comparisons, use `run-all --trials 5` or more and report:

- mean tasks passed and its 95% confidence interval
- trial count and observed range
- mean score
- seconds per task rather than only aggregate corpus time
- timeout rate
- common failure classes

## Versioning The Corpus

Changing a task prompt, starter, evaluator, or reference solution changes the benchmark. Treat corpus changes as benchmark-version changes.

Suggested policy:

- Patch version: docs or harness-only changes.
- Minor version: new tasks added, no existing tasks changed.
- Major version: existing task behavior or scoring changed.

## Avoiding Leakage

The hidden evaluator is intentionally outside the copied workdir. Do not give the agent paths to `tasks/<id>/tests/check.sh`. Do not include hidden assertions in `prompt.md`.

For public leaderboards, use a private hidden corpus in addition to the public corpus.
