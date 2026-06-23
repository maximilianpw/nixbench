# Running Agents

NixBench accepts any agent that can be invoked as a shell command.

The harness copies a task starter into a temporary directory and runs the agent command with that temporary directory as the current working directory. The agent should read `NIXBENCH_PROMPT.md`, edit local files, and exit.

The agent environment includes `NIXBENCH_TASK_ID`, `NIXBENCH_WORKDIR`, and `NIXBENCH_PROMPT`. It intentionally does not include the original task directory, hidden evaluator path, reference solution path, or score file path.

## Generic Pattern

```sh
python3 bench.py run-all \
  --agent-timeout-seconds 240 \
  --agent-cmd 'your-agent-command'
```

For one task:

```sh
python3 bench.py run package-stdenv-cli \
  --agent-timeout-seconds 240 \
  --agent-cmd 'your-agent-command'
```

## Codex

Example:

```sh
python3 bench.py run-all \
  --agent-timeout-seconds 240 \
  --agent-cmd 'codex -a never exec --ephemeral --skip-git-repo-check --sandbox workspace-write "You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop."'
```

Notes:

- `-a never` avoids interactive approval prompts.
- `--ephemeral` avoids persistent session noise.
- `--skip-git-repo-check` is useful because task workdirs are temporary copies.
- `--sandbox workspace-write` allows editing local starter files.

## Agent Prompt Contract

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
  --agent-timeout-seconds 300 \
  --agent-cmd '...'
```

Task evaluator timeouts are set in each task's `metadata.toml`:

```toml
timeout_seconds = 60
```

## Keeping Workdirs

Use `--keep-workdir` when debugging a run:

```sh
python3 bench.py run lang-attrsets-normalize \
  --keep-workdir \
  --agent-cmd '...'
```

The resulting `result.json` will include the workdir path. Without `--keep-workdir`, temporary task workdirs are removed after evaluation.

## Reading Results

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
