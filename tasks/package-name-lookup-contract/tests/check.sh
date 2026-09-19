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
  package = name: marker: { inherit name marker; };
  pkgs = {
    git = package "git" 11;
    ripgrep = package "ripgrep" 23;
    fd = package "fd" 37;
    bat = package "bat" 41;
    eza = package "eza" 53;
    nixfmt-rfc-style = package "nixfmt-rfc-style" 67;
    nil = package "nil" 79;
    statix = package "statix" 83;
    deadnix = package "deadnix" 97;
  };
  module = import ${workdir}/packages.nix { inherit pkgs; };
  packages = module.environment.systemPackages;
  required = [
    pkgs.git
    pkgs.ripgrep
    pkgs.fd
    pkgs.bat
    pkgs.eza
    pkgs.nixfmt-rfc-style
    pkgs.nil
    pkgs.statix
    pkgs.deadnix
  ];
in {
  schema_version = 2;
  criteria = {
    "core-tools" = passes (builtins.all (package: builtins.elem package packages) [ pkgs.git pkgs.ripgrep pkgs.fd ]);
    "modern-cli-tools" = passes (builtins.all (package: builtins.elem package packages) [ pkgs.bat pkgs.eza ]);
    "nix-tools" = passes (builtins.all (package: builtins.elem package packages) [ pkgs.nixfmt-rfc-style pkgs.nil pkgs.statix pkgs.deadnix ]);
    "exact-package-set" = passes (
      builtins.all (package: builtins.elem package required) packages
      && builtins.all
        (package:
          builtins.length (builtins.filter (value: value == package) packages) == 1)
        packages
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"core-tools":false,"modern-cli-tools":false,"nix-tools":false,"exact-package-set":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
