#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  legacyPackage = {
    pname = "legacylauncher";
    outPath = "/nix/store/legacylauncher";
  };
  inputs.legacylauncher.packages.x86_64-linux.legacylauncher = legacyPackage;
  pkgs = {
    system = "x86_64-linux";
    mangohud = "mangohud";
    libreoffice-fresh = "libreoffice-fresh";
  };
  module = import ${workdir}/packages.nix { inherit inputs pkgs; };
  packages = module.environment.systemPackages;
in
assert packages == [
  pkgs.mangohud
  legacyPackage
  pkgs.libreoffice-fresh
];
assert builtins.isAttrs (builtins.elemAt packages 1);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
