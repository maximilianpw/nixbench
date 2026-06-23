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
  config.services.nixbench-agent = {
    enable = true;
    package = "/nix/store/custom-agent";
    port = 9191;
    extraArgs = [ "--verbose" "--json" ];
  };
  module = import ${workdir}/module.nix {
    inherit config lib pkgs;
  };
  service = module.config.content.systemd.services.nixbench-agent;
  exec = service.serviceConfig.ExecStart;
in
assert module.options.services.nixbench-agent.enable.__enable == true;
assert module.options.services.nixbench-agent.package.default == pkgs.nixbench-agent;
assert module.options.services.nixbench-agent.port.default == 8080;
assert module.options.services.nixbench-agent.extraArgs.default == [];
assert module.config.__mkIf == true;
assert service.wantedBy == [ "multi-user.target" ];
assert builtins.match ".*custom-agent/bin/nixbench-agent.*" exec != null;
assert builtins.match ".*--port 9191.*" exec != null;
assert builtins.match ".*--verbose --json.*" exec != null;
assert module.config.content.networking.firewall.allowedTCPPorts == [ 9191 ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
