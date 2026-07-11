#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  flake = import ${workdir}/flake.nix;
  hmModule = { module = "home-manager-nixos-module"; marker = 113; };
  fakeInputs = {
    nixpkgs = {
      lib.nixosSystem = args: args;
    };
    home-manager = {
      nixosModules.home-manager = hmModule;
    };
    nixvim = {
      homeManagerModules.nixvim = { module = "nixvim-home-module"; marker = 127; };
    };
    agenix = {
      homeManagerModules.default = { module = "agenix-home-module"; marker = 131; };
    };
    benchmarkSentinel = { token = "opaque-input"; marker = 137; };
  };
  outputs = flake.outputs fakeInputs;
  cfg = outputs.nixosConfigurations.nixbench;
  hmInline =
    builtins.head
      (builtins.filter
        (module: builtins.isAttrs module && builtins.hasAttr "home-manager" module)
        cfg.modules);
  hmCfg = hmInline.home-manager;
  alice = hmCfg.users.alice { inputs = fakeInputs; };
in
assert cfg.system == "x86_64-linux";
assert cfg.specialArgs.inputs.nixvim.homeManagerModules.nixvim == fakeInputs.nixvim.homeManagerModules.nixvim;
assert cfg.specialArgs.inputs.agenix.homeManagerModules.default == fakeInputs.agenix.homeManagerModules.default;
assert cfg.specialArgs.inputs.benchmarkSentinel == fakeInputs.benchmarkSentinel;
assert builtins.elem hmModule cfg.modules;
assert hmCfg.useGlobalPkgs == true;
assert hmCfg.useUserPackages == true;
assert hmCfg.extraSpecialArgs.inputs.nixvim.homeManagerModules.nixvim == fakeInputs.nixvim.homeManagerModules.nixvim;
assert hmCfg.extraSpecialArgs.inputs.agenix.homeManagerModules.default == fakeInputs.agenix.homeManagerModules.default;
assert hmCfg.extraSpecialArgs.inputs.benchmarkSentinel == fakeInputs.benchmarkSentinel;
assert builtins.isFunction hmCfg.users.alice;
assert alice.imports == [
  fakeInputs.nixvim.homeManagerModules.nixvim
  fakeInputs.agenix.homeManagerModules.default
];
assert alice.programs.git.enable == true;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
