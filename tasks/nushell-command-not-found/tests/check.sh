#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.mkIf = condition: content: {
    __mkIf = condition;
    inherit content;
  };
  pkgs.nix-index = "/nix/store/nix-index";
  enabledConfig = {
    programs.command-not-found.enable = true;
    programs.nushell.enable = true;
  };
  disabledConfig = {
    programs.command-not-found.enable = true;
    programs.nushell.enable = false;
  };
  enabledModule = import ${workdir}/module.nix {
    config = enabledConfig;
    inherit lib pkgs;
  };
  disabledModule = import ${workdir}/module.nix {
    config = disabledConfig;
    inherit lib pkgs;
  };
  enabled = enabledModule.config.content;
  disabled = disabledModule.config.content;
  nu = enabled.programs.nushell.extraConfig;
in
assert enabledModule.config.__mkIf == true;
assert builtins.match ".*command-not-found[.]sh.*" enabled.programs.bash.interactiveShellInit != null;
assert builtins.elem pkgs.nix-index enabled.environment.systemPackages;
assert nu.__mkIf == true;
assert builtins.match ".*hooks[.]command_not_found.*" nu.content != null;
assert builtins.match ".*/nix/store/nix-index/bin/command-not-found.*" nu.content != null;
assert builtins.match ".*append __nix_command_not_found.*" nu.content != null;
assert disabled.programs.nushell.extraConfig.__mkIf == false;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
