#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
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
in {
  schema_version = 2;
  criteria = {
    "nixos-system" = passes (cfg.system == "x86_64-linux");
    "module-integration" = passes (
      builtins.elem hmModule cfg.modules
      && hmCfg.useGlobalPkgs == true && hmCfg.useUserPackages == true
      && builtins.isFunction hmCfg.users.alice
    );
    "forwards-inputs" = passes (
      cfg.specialArgs.inputs.nixvim.homeManagerModules.nixvim == fakeInputs.nixvim.homeManagerModules.nixvim
      && cfg.specialArgs.inputs.agenix.homeManagerModules.default == fakeInputs.agenix.homeManagerModules.default
      && cfg.specialArgs.inputs.benchmarkSentinel == fakeInputs.benchmarkSentinel
      && hmCfg.extraSpecialArgs.inputs.nixvim.homeManagerModules.nixvim == fakeInputs.nixvim.homeManagerModules.nixvim
      && hmCfg.extraSpecialArgs.inputs.agenix.homeManagerModules.default == fakeInputs.agenix.homeManagerModules.default
      && hmCfg.extraSpecialArgs.inputs.benchmarkSentinel == fakeInputs.benchmarkSentinel
    );
    "user-imports" = passes (
      alice.imports == [ fakeInputs.nixvim.homeManagerModules.nixvim fakeInputs.agenix.homeManagerModules.default ]
      && alice.programs.git.enable == true
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"nixos-system":false,"module-integration":false,"forwards-inputs":false,"user-imports":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
