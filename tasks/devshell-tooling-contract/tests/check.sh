#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  mkShell = attrs: attrs // { __shell = true; };
  makeTool = name: { __tool = name; };
  alejandraTool = makeTool "alejandra";
  baseArgs = {
    inherit mkShell;
    nixfmt-rfc-style = makeTool "nixfmt-rfc-style";
    statix = makeTool "statix";
    deadnix = makeTool "deadnix";
    nil = makeTool "nil";
  };
  withoutAlejandra = import ${workdir}/shell.nix baseArgs;
  withAlejandra = import ${workdir}/shell.nix (baseArgs // { alejandra = alejandraTool; });
  requiredTools = [
    baseArgs.nixfmt-rfc-style
    baseArgs.statix
    baseArgs.deadnix
    baseArgs.nil
  ];
in
assert withoutAlejandra.__shell == true;
assert withAlejandra.__shell == true;
assert withoutAlejandra.name == "nixbench-dev";
assert withAlejandra.name == "nixbench-dev";
assert builtins.all (tool: builtins.elem tool withoutAlejandra.packages) requiredTools;
assert !(builtins.elem null withoutAlejandra.packages);
assert builtins.all (tool: builtins.elem tool withAlejandra.packages) requiredTools;
assert builtins.elem alejandraTool withAlejandra.packages;
assert withoutAlejandra.NIXBENCH_FORMATTER == "nixfmt-rfc-style";
assert withAlejandra.NIXBENCH_FORMATTER == "nixfmt-rfc-style";
assert builtins.match "((.|\n)*\n)?[[:space:]]*(export[[:space:]]+)?NIX_CONFIG[[:space:]]*=[^\n]*experimental-features[^\n]*(nix-command[^\n]*flakes|flakes[^\n]*nix-command)[^\n]*(\n(.|\n)*)?" withoutAlejandra.shellHook != null;
assert builtins.match "((.|\n)*\n)?[[:space:]]*(export[[:space:]]+)?NIX_CONFIG[[:space:]]*=[^\n]*experimental-features[^\n]*(nix-command[^\n]*flakes|flakes[^\n]*nix-command)[^\n]*(\n(.|\n)*)?" withAlejandra.shellHook != null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
