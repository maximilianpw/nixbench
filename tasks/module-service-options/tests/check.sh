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
  lib = {
    mkEnableOption = description: {
      __enable = true;
      inherit description;
      default = false;
    };
    mkOption = attrs: attrs // { __option = true; };
    mkIf = condition: content: {
      __mkIf = condition;
      inherit content;
    };
    types = rec {
      package = "package";
      port = "port";
      str = "str";
      listOf = type: { inherit type; kind = "list"; };
    };
  };
  pkgs.nixbench-agent = "/nix/store/nixbench-agent";
  evaluate = serviceConfig: import ${workdir}/module.nix {
    config.services.nixbench-agent = serviceConfig;
    inherit lib pkgs;
  };
  module = evaluate {
    enable = true;
    package = "/nix/store/custom-agent";
    port = 9191;
    extraArgs = [ "--verbose" "--json" ];
  };
  alternate = evaluate {
    enable = true;
    package = "/nix/store/alternate-agent";
    port = 4242;
    extraArgs = [ "--quiet" ];
  };
  disabled = evaluate {
    enable = false;
    package = "/nix/store/disabled-agent";
    port = 3131;
    extraArgs = [];
  };
  service = module.config.content.systemd.services.nixbench-agent;
  exec = service.serviceConfig.ExecStart;
  alternateService = alternate.config.content.systemd.services.nixbench-agent;
  alternateExec = alternateService.serviceConfig.ExecStart;
in {
  schema_version = 2;
  criteria = {
    "option-schema" = passes (
      module.options.services.nixbench-agent.enable.__enable == true
      && module.options.services.nixbench-agent.package.__option == true
      && module.options.services.nixbench-agent.package.type == lib.types.package
      && module.options.services.nixbench-agent.package.default == pkgs.nixbench-agent
      && module.options.services.nixbench-agent.port.__option == true
      && module.options.services.nixbench-agent.port.type == lib.types.port
      && module.options.services.nixbench-agent.port.default == 8080
      && module.options.services.nixbench-agent.extraArgs.__option == true
      && module.options.services.nixbench-agent.extraArgs.type.kind == "list"
      && module.options.services.nixbench-agent.extraArgs.type.type == lib.types.str
      && module.options.services.nixbench-agent.extraArgs.default == []
    );
    "conditional-service" = passes (
      module.config.__mkIf == true && alternate.config.__mkIf == true && disabled.config.__mkIf == false
    );
    "exec-arguments" = passes (
      builtins.match ".*custom-agent/bin/nixbench-agent.*" exec != null
      && builtins.match ".*--port 9191.*" exec != null
      && builtins.match ".*--verbose.*" exec != null
      && builtins.match ".*--json.*" exec != null
      && builtins.match ".*alternate-agent/bin/nixbench-agent.*" alternateExec != null
      && builtins.match ".*--port 4242.*" alternateExec != null
      && builtins.match ".*--quiet.*" alternateExec != null
    );
    "firewall-port" = passes (
      module.config.content.networking.firewall.allowedTCPPorts == [ 9191 ]
      && alternate.config.content.networking.firewall.allowedTCPPorts == [ 4242 ]
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"option-schema":false,"conditional-service":false,"exec-arguments":false,"firewall-port":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
