# Scoring

NixBench uses task-level objective scoring first.

Default scoring:

- Evaluator exits `0`: full `max_score`.
- Evaluator exits non-zero or times out: `0`.
- Agent times out: the run is marked failed and receives `0` by default.

Evaluators can provide partial credit by writing JSON to `$NIXBENCH_SCORE_FILE`, which is an evaluator-only absolute path:

```json
{
  "score": 70,
  "max_score": 100,
  "notes": [
    "evaluation passes",
    "metadata missing mainProgram"
  ]
}
```

The harness records this detail in `result.json`.

Evaluator-provided scores are clamped to the task's `[0, max_score]` range. Partial credit can be recorded even when the evaluator exits non-zero or the agent timed out, but `passed` remains false unless the agent completed and the evaluator exited `0`.

If no score file exists, the evaluator exit status determines the default score. Once an evaluator creates a score file, it must be a reasonably sized regular file containing valid UTF-8 JSON with either a finite JSON number or an object with a finite numeric `score` field. Symlinks, streams, empty, oversized, malformed, excessively nested, boolean, numeric-string, non-finite, and unsupported payloads fail closed with zero credit. Invalid score details are still recorded in JSON-safe form for diagnosis.

## Recommended Rubric

For larger tasks, split hidden checks roughly like this:

- 70% functional correctness: evaluation, build behavior, generated config, or expected attributes.
- 15% Nix idiom: correct use of `mkIf`, `overrideAttrs`, fixed-output fetchers, phases, and per-system helpers.
- 10% maintainability: minimal unrelated changes, readable structure, clear attr names.
- 5% formatting and lint: `nixfmt-rfc-style`, `statix`, and `deadnix` where applicable.

Keep the public prompt stable. Add hidden cases when models overfit obvious examples.

## Failure Classes

When analyzing failed runs, tag failures with one or more classes:

- `timeout`: the agent exceeded `--agent-timeout-seconds`.
- `syntax`: Nix parsing failed.
- `evaluation`: Nix parsed but evaluation failed.
- `missing-attr`: required attribute was absent.
- `wrong-value`: required attribute existed but had the wrong value.
- `unavailable-helper`: solution used helpers not present in the evaluator.
- `impurity`: solution referenced host paths, environment variables, or external state.
- `overfit`: solution hardcoded the visible example and failed hidden inputs.

These tags are not enforced by the harness yet, but they are useful for comparing models.

## Reporting Results

A useful result report should include:

- NixBench commit.
- Agent command.
- Model name.
- Timeout.
- Overall score.
- Per-task pass/fail.
- Per-task duration.
- Failure classes.
- Links to `check.log` and `diff.patch` for failed tasks.
