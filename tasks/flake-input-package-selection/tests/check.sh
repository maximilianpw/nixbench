#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makePackage = name: system: {
    __package = name;
    inherit system;
  };
  legacyPackages = {
    x86_64-linux.legacylauncher = makePackage "legacylauncher" "x86_64-linux";
    aarch64-darwin.legacylauncher = makePackage "legacylauncher" "aarch64-darwin";
  };
  inputs.legacylauncher.packages = legacyPackages;
  linuxPkgs = {
    system = "x86_64-linux";
    mangohud = makePackage "mangohud" "x86_64-linux";
    libreoffice-fresh = makePackage "libreoffice-fresh" "x86_64-linux";
  };
  darwinPkgs = {
    system = "aarch64-darwin";
    mangohud = makePackage "mangohud" "aarch64-darwin";
    libreoffice-fresh = makePackage "libreoffice-fresh" "aarch64-darwin";
  };
  linuxPackages = (import ${workdir}/packages.nix {
    inherit inputs;
    pkgs = linuxPkgs;
  }).environment.systemPackages;
  darwinPackages = (import ${workdir}/packages.nix {
    inherit inputs;
    pkgs = darwinPkgs;
  }).environment.systemPackages;
  hasExpectedPackages = pkgs: legacyPackage: packages:
    builtins.all (package: builtins.elem package packages) [
      pkgs.mangohud
      legacyPackage
      pkgs.libreoffice-fresh
    ];
in
assert hasExpectedPackages linuxPkgs legacyPackages.x86_64-linux.legacylauncher linuxPackages;
assert hasExpectedPackages darwinPkgs legacyPackages.aarch64-darwin.legacylauncher darwinPackages;
assert builtins.all builtins.isAttrs linuxPackages;
assert builtins.all builtins.isAttrs darwinPackages;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
