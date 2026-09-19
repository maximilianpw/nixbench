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
  pkgs = {
    ripgrep = { package = "ripgrep"; marker = 107; };
    fd = { package = "fd"; marker = 109; };
  };
  outputs = import ${workdir}/shared.nix { inherit pkgs; };
  moduleArgs = { inherit pkgs; lib = {}; config = {}; };
  moduleConfig = module:
    let evaluated = if builtins.isFunction module then module moduleArgs else module;
    in evaluated.config or evaluated;
  nixos = moduleConfig outputs.nixosModule;
  home = moduleConfig outputs.homeManagerModule;
  darwin = moduleConfig outputs.darwinModule;
  count = needle: values:
    builtins.length (builtins.filter (value: value == needle) values);
  samePackages = left: right:
    builtins.length left == builtins.length right
    && builtins.all
      (package: count package left == count package right)
      (left ++ right);
  requiredPackages = [ pkgs.ripgrep pkgs.fd ];
in {
  schema_version = 2;
  criteria = {
    "shared-data" = passes (
      samePackages outputs.shared.packages requiredPackages
      && outputs.shared.shell == "fish"
    );
    "nixos-module" = passes (
      nixos.programs.fish.enable == true
      && samePackages nixos.environment.systemPackages requiredPackages
      && !(nixos ? home)
    );
    "home-manager-module" = passes (
      home.programs.fish.enable == true
      && samePackages home.home.packages requiredPackages
      && !(home ? environment)
    );
    "darwin-module" = passes (
      darwin.programs.fish.enable == true
      && samePackages darwin.environment.systemPackages requiredPackages
      && !(darwin ? home)
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"shared-data":false,"nixos-module":false,"home-manager-module":false,"darwin-module":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
