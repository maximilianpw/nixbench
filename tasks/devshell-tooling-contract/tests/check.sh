#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  mkShell = attrs: attrs // { __shell = true; };
  baseArgs = {
    inherit mkShell;
    nixfmt-rfc-style = "nixfmt-rfc-style";
    statix = "statix";
    deadnix = "deadnix";
    nil = "nil";
  };
  withoutAlejandra = import ${workdir}/shell.nix baseArgs;
  withAlejandra = import ${workdir}/shell.nix (baseArgs // { alejandra = "alejandra"; });
in
assert withoutAlejandra.__shell == true;
assert withoutAlejandra.name == "nixbench-dev";
assert withoutAlejandra.packages == [ "nixfmt-rfc-style" "statix" "deadnix" "nil" ];
assert withAlejandra.packages == [ "nixfmt-rfc-style" "statix" "deadnix" "nil" "alejandra" ];
assert withoutAlejandra.NIXBENCH_FORMATTER == "nixfmt-rfc-style";
assert builtins.match ".*nix-command flakes.*" withoutAlejandra.shellHook != null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
