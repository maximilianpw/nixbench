#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
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
in
assert result.defaultSystem == "aarch64-darwin";
assert result.names == [ "nil" "old" "ripgrep" "shellcheck" ];
assert result.versions.shellcheck == "unknown";
assert result.bySystem.x86_64-linux == [ "nil" "ripgrep" "shellcheck" ];
assert result.bySystem.aarch64-linux == [ "nil" ];
assert result.bySystem.aarch64-darwin == [ "nil" "ripgrep" ];
assert result.defaultPackages == [ "nil" "ripgrep" ];
assert empty.defaultSystem == "aarch64-darwin";
assert empty.names == [];
assert empty.versions == {};
assert empty.bySystem == {
  x86_64-linux = [];
  aarch64-linux = [];
  aarch64-darwin = [];
};
assert empty.defaultPackages == [];
assert defaultResult.defaultSystem == "x86_64-linux";
assert builtins.attrNames defaultResult.bySystem == [
  "aarch64-darwin"
  "aarch64-linux"
  "x86_64-linux"
];
assert defaultResult.defaultPackages == [ "sample" ];
assert sentinelResult.defaultSystem == "loongarch64-linux";
assert sentinelResult.bySystem == {
  riscv64-linux = [ "portable" "riscvOnly" ];
  loongarch64-linux = [ "portable" ];
};
assert sentinelResult.defaultPackages == [ "portable" ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
