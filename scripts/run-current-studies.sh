#!/bin/sh
set -u

target_trials=${NIXBENCH_TRIALS:-5}
results_dir=${NIXBENCH_RESULTS_DIR:-results}
task_count=29
prompt='You are in a temporary NixBench benchmark task workspace. Read NIXBENCH_PROMPT.md, then edit the local starter files to satisfy it. Only modify files in this directory. Do not inspect hidden evaluator files or the original task directory. Run local checks if useful, then stop.'

mkdir -p "$results_dir/study-logs"

completed_trials() {
  python3 bench.py \
    --results-dir "$results_dir" \
    study-count \
    --series "$1" \
    --effort "$2" \
    --task-count "$task_count"
}

run_trial() {
  model=$1
  series=$2
  effort=$3
  marker=$4
  label=$5
  log_path="$results_dir/study-logs/$series-$effort.log"
  completed=$(completed_trials "$series" "$effort") || return $?
  if [ "$completed" -ge "$target_trials" ]; then
    return 0
  fi

  agent_cmd="codex exec --ephemeral --skip-git-repo-check --sandbox workspace-write -m $model -c model_reasoning_effort=\"$effort\" \"$prompt\""
  next=$((completed + 1))
  printf 'starting %s / %s trial %s/%s\n' "$model" "$effort" "$next" "$target_trials" | tee -a "$log_path"

  if python3 -u bench.py \
    --results-dir "$results_dir" \
    run-all \
    --trials 1 \
    --model "$model" \
    --series "$series" \
    --effort "$effort" \
    --kind codex \
    --marker "$marker" \
    --label "$label" \
    --agent-version "$(codex --version)" \
    --network unknown \
    --agent-timeout-seconds 240 \
    --agent-cmd "$agent_cmd" >> "$log_path" 2>&1
  then
    return 0
  else
    status=$?
    if [ "$status" -eq 1 ]; then
      return 0
    fi
    printf 'study aborted with infrastructure status %s\n' "$status" | tee -a "$log_path"
    return "$status"
  fi
}

all_complete() {
  [ "$(completed_trials gpt56Sol low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Sol medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Sol high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Sol xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Sol max)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Terra low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Terra medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Terra high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Terra xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Luna low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Luna medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Luna high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Luna xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt56Luna max)" -ge "$target_trials" ]
}

while ! all_complete; do
  run_trial gpt-5.6-sol gpt56Sol low SL 'GPT-5.6 Sol via Codex CLI' || exit $?
  run_trial gpt-5.6-sol gpt56Sol medium SM 'GPT-5.6 Sol via Codex CLI' || exit $?
  run_trial gpt-5.6-sol gpt56Sol high SH 'GPT-5.6 Sol via Codex CLI' || exit $?
  run_trial gpt-5.6-sol gpt56Sol xhigh SX 'GPT-5.6 Sol via Codex CLI' || exit $?
  run_trial gpt-5.6-sol gpt56Sol max S+ 'GPT-5.6 Sol via Codex CLI' || exit $?

  run_trial gpt-5.6-terra gpt56Terra low TL 'GPT-5.6 Terra via Codex CLI' || exit $?
  run_trial gpt-5.6-terra gpt56Terra medium TM 'GPT-5.6 Terra via Codex CLI' || exit $?
  run_trial gpt-5.6-terra gpt56Terra high TH 'GPT-5.6 Terra via Codex CLI' || exit $?
  run_trial gpt-5.6-terra gpt56Terra xhigh TX 'GPT-5.6 Terra via Codex CLI' || exit $?

  run_trial gpt-5.6-luna gpt56Luna low LL 'GPT-5.6 Luna via Codex CLI' || exit $?
  run_trial gpt-5.6-luna gpt56Luna medium LM 'GPT-5.6 Luna via Codex CLI' || exit $?
  run_trial gpt-5.6-luna gpt56Luna high LH 'GPT-5.6 Luna via Codex CLI' || exit $?
  run_trial gpt-5.6-luna gpt56Luna xhigh LX 'GPT-5.6 Luna via Codex CLI' || exit $?
  run_trial gpt-5.6-luna gpt56Luna max L+ 'GPT-5.6 Luna via Codex CLI' || exit $?
done

printf 'all current-corpus studies reached %s trials\n' "$target_trials"
