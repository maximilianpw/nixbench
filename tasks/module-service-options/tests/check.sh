#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
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
in
assert module.options.services.nixbench-agent.enable.__enable == true;
assert module.options.services.nixbench-agent.package.__option == true;
assert module.options.services.nixbench-agent.package.type == lib.types.package;
assert module.options.services.nixbench-agent.package.default == pkgs.nixbench-agent;
assert module.options.services.nixbench-agent.port.__option == true;
assert module.options.services.nixbench-agent.port.type == lib.types.port;
assert module.options.services.nixbench-agent.port.default == 8080;
assert module.options.services.nixbench-agent.extraArgs.__option == true;
assert module.options.services.nixbench-agent.extraArgs.type.kind == "list";
assert module.options.services.nixbench-agent.extraArgs.type.type == lib.types.str;
assert module.options.services.nixbench-agent.extraArgs.default == [];
assert module.config.__mkIf == true;
assert alternate.config.__mkIf == true;
assert disabled.config.__mkIf == false;
assert builtins.match ".*custom-agent/bin/nixbench-agent.*" exec != null;
assert builtins.match ".*--port 9191.*" exec != null;
assert builtins.match ".*--verbose --json.*" exec != null;
assert module.config.content.networking.firewall.allowedTCPPorts == [ 9191 ];
assert builtins.match ".*alternate-agent/bin/nixbench-agent.*" alternateExec != null;
assert builtins.match ".*--port 4242.*" alternateExec != null;
assert builtins.match ".*--quiet.*" alternateExec != null;
assert alternate.config.content.networking.firewall.allowedTCPPorts == [ 4242 ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
