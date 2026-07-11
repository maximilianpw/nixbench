#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.licenses = {
    asl20 = { spdxId = "Apache-2.0"; marker = 20; };
    mit = { spdxId = "MIT"; marker = 21; };
    bsd3 = { spdxId = "BSD-3-Clause"; marker = 22; };
    gpl3Only = { spdxId = "GPL-3.0-only"; marker = 23; };
  };
  python3Packages = rec {
    buildPythonApplication = attrs: attrs // { __builder = "buildPythonApplication"; };
    hatchling = { package = "hatchling"; marker = 31; };
    click = { package = "click"; marker = 37; };
    rich = { package = "rich"; marker = 41; };
    pytest = { package = "pytest"; marker = 43; };
  };
  pkg = import ${workdir}/default.nix {
    inherit lib python3Packages;
  };
in
assert pkg.__builder == "buildPythonApplication";
assert pkg.pname == "nixbench-report";
assert pkg.version == "0.2.0";
assert pkg.pyproject == true;
assert builtins.elem python3Packages.hatchling pkg.nativeBuildInputs;
assert builtins.all (dependency: builtins.elem dependency pkg.propagatedBuildInputs) [
  python3Packages.click
  python3Packages.rich
];
assert builtins.elem python3Packages.pytest pkg.nativeCheckInputs;
assert pkg.pythonImportsCheck == [ "nixbench_report" ];
assert pkg.pytestFlagsArray == [ "tests" ];
assert pkg.meta ? description;
assert builtins.isString pkg.meta.description;
assert pkg.meta.description != "";
assert pkg.meta ? homepage;
assert builtins.isString pkg.meta.homepage;
assert pkg.meta.homepage != "";
assert pkg.meta.license == lib.licenses.asl20;
assert pkg.meta.mainProgram == "nixbench-report";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
