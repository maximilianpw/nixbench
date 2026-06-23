#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  pkgs = {
    ripgrep = "ripgrep";
    fd = "fd";
  };
  outputs = import ${workdir}/shared.nix { inherit pkgs; };
  nixos = outputs.nixosModule {};
  home = outputs.homeManagerModule {};
  darwin = outputs.darwinModule {};
in
assert outputs.shared.packages == [ pkgs.ripgrep pkgs.fd ];
assert outputs.shared.shell == "fish";
assert nixos.programs.fish.enable == true;
assert nixos.environment.systemPackages == outputs.shared.packages;
assert !(nixos ? home);
assert home.programs.fish.enable == true;
assert home.home.packages == outputs.shared.packages;
assert !(home ? environment);
assert darwin.programs.fish.enable == true;
assert darwin.environment.systemPackages == outputs.shared.packages;
assert !(darwin ? home);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
