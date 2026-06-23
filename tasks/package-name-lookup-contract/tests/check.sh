#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  pkgs = {
    git = "git";
    ripgrep = "ripgrep";
    fd = "fd";
    bat = "bat";
    eza = "eza";
    nixfmt-rfc-style = "nixfmt-rfc-style";
    nil = "nil";
    statix = "statix";
    deadnix = "deadnix";
  };
  module = import ${workdir}/packages.nix { inherit pkgs; };
  packages = module.environment.systemPackages;
  required = [
    "git"
    "ripgrep"
    "fd"
    "bat"
    "eza"
    "nixfmt-rfc-style"
    "nil"
    "statix"
    "deadnix"
  ];
in
assert builtins.length packages == builtins.length required;
assert builtins.all (package: builtins.elem package packages) required;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
