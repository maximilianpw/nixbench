#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  package = name: marker: { inherit name marker; };
  pkgs = {
    git = package "git" 11;
    ripgrep = package "ripgrep" 23;
    fd = package "fd" 37;
    bat = package "bat" 41;
    eza = package "eza" 53;
    nixfmt-rfc-style = package "nixfmt-rfc-style" 67;
    nil = package "nil" 79;
    statix = package "statix" 83;
    deadnix = package "deadnix" 97;
  };
  module = import ${workdir}/packages.nix { inherit pkgs; };
  packages = module.environment.systemPackages;
  required = [
    pkgs.git
    pkgs.ripgrep
    pkgs.fd
    pkgs.bat
    pkgs.eza
    pkgs.nixfmt-rfc-style
    pkgs.nil
    pkgs.statix
    pkgs.deadnix
  ];
in
assert builtins.length packages == builtins.length required;
assert builtins.all (package: builtins.elem package packages) required;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
