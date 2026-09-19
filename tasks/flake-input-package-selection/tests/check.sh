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
  makePackage = name: system: selection: {
    __package = name;
    inherit system;
    inherit selection;
  };
  legacyPackages = {
    x86_64-linux = {
      legacylauncher = makePackage "legacylauncher" "x86_64-linux" "named";
      default = makePackage "legacylauncher-default" "x86_64-linux" "default";
    };
    aarch64-darwin = {
      legacylauncher = makePackage "legacylauncher" "aarch64-darwin" "named";
      default = makePackage "legacylauncher-default" "aarch64-darwin" "default";
    };
  };
  inputs.legacylauncher.packages = legacyPackages;
  linuxPkgs = {
    system = "x86_64-linux";
    mangohud = makePackage "mangohud" "x86_64-linux" "platform";
    libreoffice-fresh = makePackage "libreoffice-fresh" "x86_64-linux" "platform";
  };
  darwinPkgs = {
    system = "aarch64-darwin";
    mangohud = makePackage "mangohud" "aarch64-darwin" "platform";
    libreoffice-fresh = makePackage "libreoffice-fresh" "aarch64-darwin" "platform";
  };
  observePackages = pkgs:
    let
      candidate = import ${workdir}/packages.nix { inherit inputs pkgs; };
      packages = candidate.environment.systemPackages;
      attempted = builtins.tryEval (builtins.deepSeq packages packages);
    in if attempted.success && builtins.isList attempted.value
       then attempted.value
       else [];
  linuxPackages = observePackages linuxPkgs;
  darwinPackages = observePackages darwinPkgs;
  hasPlatformPackages = pkgs: packages:
    builtins.isList packages
    && builtins.all (package: builtins.elem package packages) [
      pkgs.mangohud
      pkgs.libreoffice-fresh
    ];
in {
  schema_version = 2;
  criteria = {
    "linux-packages" = passes (
      hasPlatformPackages linuxPkgs linuxPackages
    );
    "darwin-packages" = passes (
      hasPlatformPackages darwinPkgs darwinPackages
    );
    "named-input-output" = passes (
      builtins.elem legacyPackages.x86_64-linux.legacylauncher linuxPackages
      && builtins.elem legacyPackages.aarch64-darwin.legacylauncher darwinPackages
      && !(builtins.elem legacyPackages.x86_64-linux.default linuxPackages)
      && !(builtins.elem legacyPackages.aarch64-darwin.default darwinPackages)
    );
    "package-values" = passes (
      builtins.length linuxPackages == 3
      && builtins.length darwinPackages == 3
      && builtins.all builtins.isAttrs linuxPackages
      && builtins.all builtins.isAttrs darwinPackages
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"linux-packages":false,"darwin-packages":false,"named-input-output":false,"package-values":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
