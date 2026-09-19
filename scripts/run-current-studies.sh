#!/bin/sh
set -u

target_trials=${NIXBENCH_TRIALS:-5}
results_dir=${NIXBENCH_RESULTS_DIR:-results}
wrapper_prompt_file=protocols/agent-wrapper.txt
nix_system=$(python3 -c 'from nixbench.runner import detect_nix_system; print(detect_nix_system())')
codex_bin=$(command -v codex)

mkdir -p "$results_dir/study-logs"
mkdir -p "$results_dir/study-protocols"

protocol_file() {
  model=$1
  series=$2
  effort=$3
  path="$results_dir/study-protocols/$series-$effort.toml"
  {
    printf 'schema_version = 2\n'
    printf 'id = "%s-%s"\n' "$series" "$effort"
    printf 'harness_id = "nixbench"\n'
    printf 'harness_version = "2.0.0"\n'
    printf 'model_id = "%s"\n' "$model"
    printf 'model_identity_evidence = "unverified"\n'
    printf 'effort = "%s"\n' "$effort"
    printf 'network_policy = "unknown"\n'
    printf 'isolation_profile = "local-workspace"\n'
    printf 'tool_policy = "codex-default"\n'
    printf 'completion_attestation = "required"\n'
    printf 'agent_adapter = "codex-json"\n'
    printf 'agent_timeout_seconds = 240\n'
    printf 'system = "%s"\n' "$nix_system"
  } > "$path"
  printf '%s\n' "$path"
}

agent_command() {
  model=$1
  effort=$2
  printf '"%s" exec --json --ephemeral --skip-git-repo-check --sandbox workspace-write -m %s -c model_reasoning_effort="%s"\n' \
    "$codex_bin" "$model" "$effort"
}

completed_trials() {
  model=$1
  series=$2
  effort=$3
  protocol=$(protocol_file "$model" "$series" "$effort")
  agent_cmd=$(agent_command "$model" "$effort")
  python3 bench.py \
    --results-dir "$results_dir" \
    study-count \
    --protocol-file "$protocol" \
    --wrapper-prompt-file "$wrapper_prompt_file" \
    --agent-timeout-seconds 240 \
    --agent-adapter codex-json \
    --agent-cmd "$agent_cmd"
}

run_trial() {
  model=$1
  series=$2
  effort=$3
  marker=$4
  label=$5
  log_path="$results_dir/study-logs/$series-$effort.log"
  protocol=$(protocol_file "$model" "$series" "$effort")
  agent_cmd=$(agent_command "$model" "$effort")
  completed=$(completed_trials "$model" "$series" "$effort") || return $?
  if [ "$completed" -ge "$target_trials" ]; then
    return 0
  fi

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
    --protocol-file "$protocol" \
    --wrapper-prompt-file "$wrapper_prompt_file" \
    --agent-timeout-seconds 240 \
    --agent-adapter codex-json \
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
  [ "$(completed_trials gpt-5.6-sol gpt56Sol low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-sol gpt56Sol medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-sol gpt56Sol high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-sol gpt56Sol xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-sol gpt56Sol max)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-terra gpt56Terra low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-terra gpt56Terra medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-terra gpt56Terra high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-terra gpt56Terra xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-luna gpt56Luna low)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-luna gpt56Luna medium)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-luna gpt56Luna high)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-luna gpt56Luna xhigh)" -ge "$target_trials" ] &&
    [ "$(completed_trials gpt-5.6-luna gpt56Luna max)" -ge "$target_trials" ]
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
