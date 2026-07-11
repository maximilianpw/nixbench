#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  merge = left: right:
    if builtins.isAttrs left && builtins.isAttrs right then
      builtins.mapAttrs
        (name: _:
          if builtins.hasAttr name left && builtins.hasAttr name right then
            merge left.${name} right.${name}
          else if builtins.hasAttr name right then
            right.${name}
          else
            left.${name})
        (left // right)
    else
      right;
  lib = {
    mkIf = condition: content: if condition then content else {};
    mkMerge = definitions: builtins.foldl' merge {} definitions;
  };
  pkgs.nix-index = "/nix/store/nix-index";
  evaluate = commandNotFoundEnabled: nushellEnabled:
    import ${workdir}/module.nix {
      config = {
        programs.command-not-found.enable = commandNotFoundEnabled;
        programs.nushell.enable = nushellEnabled;
      };
      inherit lib pkgs;
    };
  enabled = (evaluate true true).config;
  withoutNushell = (evaluate true false).config;
  disabled = (evaluate false true).config;
  nuConfig = enabled.programs.nushell.extraConfig;
  nuCode = builtins.concatStringsSep "\n" (
    builtins.filter
      (line:
        builtins.isString line
        && builtins.match "[[:space:]]*#.*" line == null)
      (builtins.split "\n" nuConfig)
  );
  disabledNuConfig = withoutNushell.programs.nushell.extraConfig or {};
in
assert builtins.match ".*command-not-found[.]sh.*" enabled.programs.bash.interactiveShellInit != null;
assert builtins.match ".*command-not-found[.]sh.*" withoutNushell.programs.bash.interactiveShellInit != null;
assert builtins.elem pkgs.nix-index enabled.environment.systemPackages;
assert builtins.isString nuConfig;
assert builtins.match "(.|\n)*(upsert[[:space:]]+hooks[.]command_not_found|hooks[.]command_not_found[[:space:]]*=)(.|\n)*(append|/nix/store/nix-index/bin/command-not-found)(.|\n)*" nuCode != null;
assert builtins.match "(.|\n)*/nix/store/nix-index/bin/command-not-found[[:space:]]+[$]?[A-Za-z_][A-Za-z0-9_]*(.|\n)*" nuCode != null;
assert builtins.match "(.|\n)*hooks[.]command_not_found[[:space:]]*=[[:space:]]*\[[[:space:]]*\](.|\n)*" nuCode == null;
assert disabledNuConfig == {};
assert disabled == {};
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
