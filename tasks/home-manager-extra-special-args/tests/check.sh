#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  flake = import ${workdir}/flake.nix;
  hmModule = "home-manager-nixos-module";
  fakeInputs = {
    nixpkgs = {
      lib.nixosSystem = args: args;
    };
    home-manager = {
      nixosModules.home-manager = hmModule;
    };
    nixvim = {
      homeManagerModules.nixvim = "nixvim-home-module";
    };
    agenix = {
      homeManagerModules.default = "agenix-home-module";
    };
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
assert cfg.specialArgs.inputs.nixvim.homeManagerModules.nixvim == "nixvim-home-module";
assert cfg.specialArgs.inputs.agenix.homeManagerModules.default == "agenix-home-module";
assert builtins.elem hmModule cfg.modules;
assert hmCfg.useGlobalPkgs == true;
assert hmCfg.useUserPackages == true;
assert hmCfg.extraSpecialArgs.inputs.nixvim.homeManagerModules.nixvim == "nixvim-home-module";
assert hmCfg.extraSpecialArgs.inputs.agenix.homeManagerModules.default == "agenix-home-module";
assert builtins.isFunction hmCfg.users.alice;
assert alice.imports == [ "nixvim-home-module" "agenix-home-module" ];
assert alice.programs.git.enable == true;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
