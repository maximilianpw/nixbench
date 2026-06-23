#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.licenses = {
    asl20 = "Apache-2.0";
    mit = "MIT";
    bsd3 = "BSD-3-Clause";
    gpl3Only = "GPL-3.0-only";
  };
  python3Packages = rec {
    buildPythonApplication = attrs: attrs // { __builder = "buildPythonApplication"; };
    hatchling = "hatchling";
    click = "click";
    rich = "rich";
    pytest = "pytest";
  };
  pkg = import ${workdir}/default.nix {
    inherit lib python3Packages;
  };
in
assert pkg.__builder == "buildPythonApplication";
assert pkg.pname == "nixbench-report";
assert pkg.version == "0.2.0";
assert pkg.pyproject == true;
assert pkg.nativeBuildInputs == [ "hatchling" ];
assert pkg.propagatedBuildInputs == [ "click" "rich" ];
assert pkg.nativeCheckInputs == [ "pytest" ];
assert pkg.pythonImportsCheck == [ "nixbench_report" ];
assert pkg.pytestFlagsArray == [ "tests" ];
assert pkg.meta ? description;
assert pkg.meta.description != "";
assert pkg.meta ? homepage;
assert pkg.meta.homepage != "";
assert pkg.meta ? license;
assert pkg.meta.mainProgram == "nixbench-report";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
