# Benchmark Design

NixBench is designed around agentic repair, not snippet generation.

A model is given an editable worktree and a task prompt. It must inspect the files, make changes, and leave the worktree in a state that passes hidden checks. This gives the benchmark room to measure practical behavior: reading requirements, editing the right file, avoiding irrelevant churn, running local checks, and handling Nix evaluation errors.

## Goals

NixBench aims to measure:

- Whether an agent can produce Nix code that evaluates.
- Whether it can distinguish common Nix contexts: flakes, modules, overlays, derivations, shells, and fetchers.
- Whether it can avoid plausible but unavailable helpers in restricted evaluators.
- Whether it can preserve existing metadata, inputs, patches, and options.
- Whether it can fix broken code rather than replacing it blindly.

## Non-Goals

NixBench does not currently try to measure:

- Large-scale nixpkgs contribution quality.
- Long-running real package builds.
- Human taste in Nix style.
- End-to-end NixOS deployment behavior.
- Cross-model leaderboard fairness across hardware and network conditions.

Those can be added later, but the initial corpus focuses on fast deterministic evaluation.

## Why Fake Builders Are Useful

Many tasks use fake builders such as:

```nix
stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
```

This pattern makes the evaluator inspect the structure of the candidate Nix expression without building a real derivation. That is useful because:

- It avoids network and cache dependence.
- It keeps task runtime low.
- It catches attr-level mistakes precisely.
- It makes hidden tests easy to author.

Real-build tasks are still useful, but they should be marked separately because they are slower and less deterministic.

## Why Hidden Evaluators Matter

If the public prompt says "include `mainProgram`", a weak model can satisfy the visible text with a string search strategy. A hidden evaluator can check semantic shape instead:

```nix
assert pkg.meta.mainProgram == "tinygrep";
```

Hidden evaluators also catch overfitting. For example, a prompt may include one package set, while the evaluator uses another package set with disabled packages, missing fields, or different system lists.

## Task Difficulty

Suggested difficulty levels:

- Easy: one file, direct requirements, no subtle Nix semantics.
- Medium: one or two files, multiple constraints, some idiom required.
- Hard: module system, overlays, recursive values, or purity constraints.

Difficulty should reflect the expected reasoning load, not the number of lines changed.

## Corpus Health Checks

Every task should satisfy two checks:

```sh
python3 bench.py validate --solution reference
python3 bench.py validate --solution starter
```

The reference should pass. The starter should usually fail. If a starter passes, the task is not measuring anything useful.
The `validate` command exits successfully only when every reference passes at full score or every starter is cleanly rejected with evaluator exit code `1` below full score, depending on the selected mode. Evaluator timeouts, invalid score files, and infrastructure exit codes are never counted as healthy starter failures. The command rejects an empty task selection rather than reporting a vacuous success.

Those two checks are only corpus smoke tests. Evaluator contract tests should additionally prove that known-invalid mutations fail and valid alternative implementations pass. This prevents hidden checks from becoming either a reference-solution snapshot or a loose shape check that can be gamed with hard-coded values.

## Benchmark Integrity

For fair runs:

- Do not expose `tests/check.sh` to the agent workdir.
- Do not expose the original task directory, reference solution, or score file path to the agent.
- Use the same timeout for every comparable agent.
- Record the exact agent command.
- Keep `summary.json`, `result.json`, `agent.log`, `check.log`, and `diff.patch`.
- Pin task corpus versions when comparing results over time.
