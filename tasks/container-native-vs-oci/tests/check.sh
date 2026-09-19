#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
  module = import ${workdir}/container.nix {};
  cfg = if module ? config then module.config else module;
  container = cfg.containers.ubuntu-lab;
  rawContainerConfig =
    if builtins.isFunction container.config
    then container.config {
      config = {};
      lib = {
        mkDefault = value: value;
        mkForce = value: value;
        mkIf = condition: value: if condition then value else {};
      };
      pkgs = { openssh = { package = "openssh"; marker = 211; }; };
    }
    else container.config;
  containerConfigAttempt = builtins.tryEval (
    builtins.deepSeq rawContainerConfig rawContainerConfig
  );
in {
  schema_version = 2;
  criteria = {
    "native-container-shape" = passes (
      container.autoStart == true
      && !((cfg ? virtualisation) && (cfg.virtualisation ? oci-containers))
    );
    "network-and-mounts" = passes (
      container.privateNetwork == true
      && container.bindMounts."/dev/bus/usb".hostPath == "/dev/bus/usb"
      && container.bindMounts."/dev/bus/usb".isReadOnly == false
    );
    "nested-service-module" = passes (
      containerConfigAttempt.success
      && containerConfigAttempt.value.services.openssh.enable == true
    );
    "no-oci-fields" = passes (!(container ? image) && !(container ? extraOptions));
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"native-container-shape":false,"network-and-mounts":false,"nested-service-module":false,"no-oci-fields":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
