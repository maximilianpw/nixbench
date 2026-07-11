#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.optional = condition: value: if condition then [ value ] else [];
  withExplicitLib = import ${workdir}/config.nix { inherit lib; };
  withDefaultLib = import ${workdir}/config.nix {};
  expected = {
    name = "nixbench";
    enableDocs = true;
    outputs = [ "nixbench" "manual" ];
  };
in
assert withExplicitLib == expected;
assert withDefaultLib == expected;
assert builtins.attrNames withDefaultLib == [ "enableDocs" "name" "outputs" ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
