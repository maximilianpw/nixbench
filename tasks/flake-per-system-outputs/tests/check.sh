#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  flake = import ${workdir}/flake.nix;
  outputs = flake.outputs { self = outputs; };
  systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
  checkSystem = system:
    let
      package = (builtins.getAttr system outputs.packages).default;
      app = (builtins.getAttr system outputs.apps).default;
      check = (builtins.getAttr system outputs.checks).eval;
      shell = (builtins.getAttr system outputs.devShells).default;
    in
    package.pname == "nixbench-sample"
    && package.version == "0.1.0"
    && package.system == system
    && app.type == "app"
    && check == package
    && shell.name == "nixbench-dev"
    && builtins.elem "nixfmt" shell.tools
    && builtins.elem "statix" shell.tools;
in
assert outputs.lib.systems == systems;
assert builtins.all checkSystem systems;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
