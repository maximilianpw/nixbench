#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  homeManagerModule = {
    module = "home-manager-nixos-module";
    marker = 103;
  };
  cfg = import ${workdir}/configuration.nix { inherit homeManagerModule; };
in
assert builtins.elem homeManagerModule cfg.imports;
assert cfg.wsl.enable == true;
assert cfg.wsl.defaultUser == "nixos";
assert cfg.home-manager.useGlobalPkgs == true;
assert cfg.home-manager.useUserPackages == true;
assert cfg.home-manager.users.nixos.programs.git.enable == true;
assert !(cfg ? homeConfiguration);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null

if sed 's/[[:space:]]*#.*$//' "$workdir/configuration.nix" \
  | grep -Eq '<home-manager/nixos>|homeManagerConfiguration'; then
  echo "configuration.nix uses a forbidden standalone or legacy Home Manager entrypoint" >&2
  exit 1
fi
