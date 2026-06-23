#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  homeManagerModule = "home-manager-nixos-module";
  cfg = import ${workdir}/configuration.nix { inherit homeManagerModule; };
in
assert cfg.imports == [ homeManagerModule ];
assert cfg.wsl.enable == true;
assert cfg.wsl.defaultUser == "nixos";
assert cfg.home-manager.useGlobalPkgs == true;
assert cfg.home-manager.useUserPackages == true;
assert cfg.home-manager.users.nixos.programs.git.enable == true;
assert !(cfg ? homeConfiguration);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
