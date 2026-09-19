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
  get = path: default: value:
    if path == [] then value
    else if builtins.isAttrs value && builtins.hasAttr (builtins.head path) value
    then get (builtins.tail path) default (builtins.getAttr (builtins.head path) value)
    else default;
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
    concatStringsSep = builtins.concatStringsSep;
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
  options = get [ "options" "services" "nixbench-agent" ] {} module;
  enableOption = get [ "enable" ] {} options;
  packageOption = get [ "package" ] {} options;
  portOption = get [ "port" ] {} options;
  extraArgsOption = get [ "extraArgs" ] {} options;
  extraArgsType = get [ "type" ] {} extraArgsOption;
  moduleConfig = get [ "config" ] {} module;
  alternateConfig = get [ "config" ] {} alternate;
  disabledConfig = get [ "config" ] {} disabled;
  service = get [ "content" "systemd" "services" "nixbench-agent" ] {} moduleConfig;
  exec = get [ "serviceConfig" "ExecStart" ] "" service;
  alternateService = get [ "content" "systemd" "services" "nixbench-agent" ] {} alternateConfig;
  alternateExec = get [ "serviceConfig" "ExecStart" ] "" alternateService;
in {
  schema_version = 2;
  criteria = {
    "option-schema" = passes (
      get [ "__enable" ] false enableOption == true
      && get [ "__option" ] false packageOption == true
      && get [ "type" ] null packageOption == lib.types.package
      && get [ "default" ] null packageOption == pkgs.nixbench-agent
      && get [ "__option" ] false portOption == true
      && get [ "type" ] null portOption == lib.types.port
      && get [ "default" ] null portOption == 8080
      && get [ "__option" ] false extraArgsOption == true
      && get [ "kind" ] null extraArgsType == "list"
      && get [ "type" ] null extraArgsType == lib.types.str
      && get [ "default" ] null extraArgsOption == []
    );
    "conditional-service" = passes (
      get [ "__mkIf" ] false moduleConfig == true
      && get [ "__mkIf" ] false alternateConfig == true
      && get [ "__mkIf" ] true disabledConfig == false
    );
    "exec-arguments" = passes (
      builtins.isString exec
      && builtins.match ".*custom-agent/bin/nixbench-agent.*" exec != null
      && builtins.match ".*--port 9191.*" exec != null
      && builtins.match ".*--verbose.*" exec != null
      && builtins.match ".*--json.*" exec != null
      && builtins.isString alternateExec
      && builtins.match ".*alternate-agent/bin/nixbench-agent.*" alternateExec != null
      && builtins.match ".*--port 4242.*" alternateExec != null
      && builtins.match ".*--quiet.*" alternateExec != null
    );
    "firewall-port" = passes (
      get [ "content" "networking" "firewall" "allowedTCPPorts" ] null moduleConfig == [ 9191 ]
      && get [ "content" "networking" "firewall" "allowedTCPPorts" ] null alternateConfig == [ 4242 ]
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"option-schema":false,"conditional-service":false,"exec-arguments":false,"firewall-port":false},"notes":[]}' >"$score_tmp"
fi
if sed 's/[[:space:]]*#.*$//' "$workdir/module.nix" | grep -Eq 'lib[.]concatStringsSep'; then
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); p["criteria"]["option-schema"]=False; json.dump(p,open(sys.argv[1],"w"),separators=(",",":"))' "$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
