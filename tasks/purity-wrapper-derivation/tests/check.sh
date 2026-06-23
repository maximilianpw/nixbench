#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
  lib = {
    makeBinPath = paths: builtins.concatStringsSep ":" (map (path: path + "/bin") paths);
    getExe = package: package + "/bin/" + builtins.baseNameOf package;
  };
  makeWrapper = "makeWrapper";
  coreutils = "/nix/store/coreutils";
  bash = "/nix/store/bash";
  drv = import ${workdir}/derivation.nix {
    inherit stdenv lib makeWrapper coreutils bash;
  };
in
assert drv.__mkDerivation == true;
assert drv.pname == "pure-runner";
assert drv.version == "1.0.0";
assert drv.nativeBuildInputs == [ makeWrapper ];
assert builtins.match ".*makeWrapper /nix/store/bash/bin/bash.*" drv.installPhase != null;
assert builtins.match ".*coreutils/bin.*" drv.installPhase != null;
assert builtins.match ".*usr/bin.*" drv.installPhase == null;
assert builtins.match ".*HOME.*" drv.installPhase == null;
assert drv.passthru.pure == true;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
