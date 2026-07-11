#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
  lib = {
    makeBinPath = paths:
      if paths == [ coreutils ]
      then "/nix/store/nixbench-coreutils-path/bin"
      else throw "makeBinPath must receive only coreutils";
  };
  makeWrapper = "makeWrapper";
  coreutils = "/nix/store/coreutils";
  bash = {
    outPath = "/nix/store/nixbench-bash-sentinel";
    __toString = self: self.outPath;
    marker = 199;
  };
  drv = import ${workdir}/derivation.nix {
    inherit stdenv lib makeWrapper coreutils bash;
  };
in
assert drv.__mkDerivation == true;
assert drv.pname == "pure-runner";
assert drv.version == "1.0.0";
assert builtins.elem makeWrapper drv.nativeBuildInputs;
assert builtins.match ".*makeWrapper /nix/store/nixbench-bash-sentinel/bin/bash.*" drv.installPhase != null;
assert builtins.match ".*nixbench-coreutils-path/bin.*" drv.installPhase != null;
assert builtins.match ".*usr/bin.*" drv.installPhase == null;
assert builtins.match ".*HOME.*" drv.installPhase == null;
assert drv.passthru.pure == true;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null

if sed 's/[[:space:]]*#.*$//' "$workdir/derivation.nix" \
  | grep -Eq "builtins[.]getEnv|lib[.]getExe|[\"']/usr/bin|[\"']/bin|\\\$HOME"; then
  echo "derivation.nix references a forbidden impure helper or host path" >&2
  exit 1
fi
