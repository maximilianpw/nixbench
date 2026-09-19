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
  normalize = import ${workdir}/lib.nix {
    allSystems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
    defaultSystem = "aarch64-darwin";
  };
  result = normalize {
    nil = { version = "2024-08-06"; };
    old = { version = "0.1.0"; disabled = true; };
    ripgrep = {
      version = "14.1.0";
      systems = [ "x86_64-linux" "aarch64-darwin" ];
    };
    shellcheck = { systems = [ "x86_64-linux" ]; };
  };
  empty = normalize {};
  normalizeDefaults = import ${workdir}/lib.nix {};
  defaultResult = normalizeDefaults {
    sample = { version = "1.0.0"; };
  };
  normalizeSentinelSystems = import ${workdir}/lib.nix {
    allSystems = [ "riscv64-linux" "loongarch64-linux" ];
    defaultSystem = "loongarch64-linux";
  };
  sentinelResult = normalizeSentinelSystems {
    portable = {};
    riscvOnly.systems = [ "riscv64-linux" ];
  };
in {
  schema_version = 2;
  criteria = {
    "names-and-versions" = passes (
      result.names == [ "nil" "old" "ripgrep" "shellcheck" ]
      && result.versions.shellcheck == "unknown"
      && empty.names == [] && empty.versions == {}
    );
    "by-system" = passes (
      result.bySystem.x86_64-linux == [ "nil" "ripgrep" "shellcheck" ]
      && result.bySystem.aarch64-linux == [ "nil" ]
      && result.bySystem.aarch64-darwin == [ "nil" "ripgrep" ]
      && empty.bySystem == { x86_64-linux = []; aarch64-linux = []; aarch64-darwin = []; }
    );
    "default-packages" = passes (
      result.defaultSystem == "aarch64-darwin"
      && result.defaultPackages == [ "nil" "ripgrep" ]
      && empty.defaultSystem == "aarch64-darwin"
      && empty.defaultPackages == []
      && defaultResult.defaultSystem == "x86_64-linux"
      && defaultResult.defaultPackages == [ "sample" ]
    );
    "parameterized-systems" = passes (
      builtins.attrNames defaultResult.bySystem == [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" ]
      && sentinelResult.defaultSystem == "loongarch64-linux"
      && sentinelResult.bySystem == { riscv64-linux = [ "portable" "riscvOnly" ]; loongarch64-linux = [ "portable" ]; }
      && sentinelResult.defaultPackages == [ "portable" ]
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"names-and-versions":false,"by-system":false,"default-packages":false,"parameterized-systems":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
