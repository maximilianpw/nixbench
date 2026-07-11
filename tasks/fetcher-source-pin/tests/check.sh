#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  fetchFromGitHub = attrs: attrs // { __fetcher = "github"; };
  src = import ${workdir}/source.nix { inherit fetchFromGitHub; };
in
assert src.__fetcher == "github";
assert src.owner == "nix-community";
assert src.repo == "nixbench-fixture";
assert builtins.match "[0-9a-f]{40}" src.rev != null;
assert builtins.isString src.hash;
assert builtins.match "sha256-[A-Za-z0-9+/]{43}=" src.hash != null;
assert src.fetchSubmodules == true;
assert src.leaveDotGit == false;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
