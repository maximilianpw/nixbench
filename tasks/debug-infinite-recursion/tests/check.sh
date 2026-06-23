#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.optional = condition: value: if condition then [ value ] else [];
  config = import ${workdir}/config.nix { inherit lib; };
in
assert config.name == "nixbench";
assert config.enableDocs == true;
assert config.outputs == [ "nixbench" "manual" ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
