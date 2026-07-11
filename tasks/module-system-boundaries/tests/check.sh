#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  pkgs = {
    ripgrep = { package = "ripgrep"; marker = 107; };
    fd = { package = "fd"; marker = 109; };
  };
  outputs = import ${workdir}/shared.nix { inherit pkgs; };
  moduleArgs = { inherit pkgs; lib = {}; config = {}; };
  moduleConfig = module:
    let evaluated = module moduleArgs;
    in evaluated.config or evaluated;
  nixos = moduleConfig outputs.nixosModule;
  home = moduleConfig outputs.homeManagerModule;
  darwin = moduleConfig outputs.darwinModule;
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
