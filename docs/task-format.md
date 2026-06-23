# Task Format

Each benchmark task lives in `tasks/<task-id>/`.

```text
tasks/<task-id>/
  metadata.toml
  prompt.md
  starter/
  reference/
  tests/
    check.sh
```

## `metadata.toml`

Required fields:

```toml
id = "package-stdenv-cli"
name = "Package A stdenv CLI"
category = "packages"
difficulty = "medium"
timeout_seconds = 60
max_score = 100
systems = ["any"]
evaluator = "tests/check.sh"
```

`systems = ["any"]` means the task is system-independent. Use Nix system names such as `x86_64-linux` or `aarch64-darwin` for system-specific tasks.

## `prompt.md`

This is the prompt copied into the workdir as `NIXBENCH_PROMPT.md`. It should describe the task requirements and expected files, but not reveal hidden evaluator details.

## `starter/`

Starter files are copied into a temporary workdir. The agent edits only this copy.

## `reference/`

Reference files are overlaid onto the starter when running:

```sh
python3 bench.py validate --solution reference
```

The reference solution should pass the evaluator and act as a regression fixture for task authors.

## `tests/check.sh`

The evaluator runs as:

```sh
/bin/sh tests/check.sh "$NIXBENCH_WORKDIR"
```

It should exit `0` for pass and non-zero for fail. It may write a JSON score to `$NIXBENCH_SCORE_FILE`:

```json
{
  "score": 80,
  "notes": ["main behavior passed", "style check failed"]
}
```

If no score file is written, the harness awards full score on pass and zero on fail.

`NIXBENCH_SCORE_FILE` is only provided to the evaluator, not to the agent command.

## Authoring Checklist

Before adding a task to the corpus:

- Run the reference solution and confirm it passes.
- Run the starter solution and confirm it fails.
- Keep evaluator assertions semantic where possible.
- Avoid network access in the evaluator unless the task is explicitly marked as a slow integration task.
- Avoid checking only for strings when Nix evaluation can inspect the value.
- Keep prompts clear about required files and expected behavior.

## Metadata Guidance

Use categories that describe the Nix skill being tested:

- `nix-language`
- `flakes`
- `packages`
- `modules`
- `overlays`
- `fetchers`
- `devshells`
- `debugging`
- `purity`

Use `systems = ["any"]` for pure evaluation tasks. Reserve real Nix systems for tasks that depend on platform-specific behavior.
