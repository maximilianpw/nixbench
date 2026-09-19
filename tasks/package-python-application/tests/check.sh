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
  runtimeInputs = (pkg.dependencies or []) ++ (pkg.propagatedBuildInputs or []);
in {
  schema_version = 2;
  criteria = {
    "package-identity" = passes (
      pkg.__builder == "buildPythonApplication" && pkg.pname == "nixbench-report"
      && pkg.version == "0.2.0" && pkg.pyproject == true
    );
    "build-and-runtime-inputs" = passes (
      builtins.elem python3Packages.hatchling pkg.nativeBuildInputs
      && builtins.all (dependency: builtins.elem dependency runtimeInputs) [ python3Packages.click python3Packages.rich ]
    );
    "test-contract" = passes (
      builtins.elem python3Packages.pytest pkg.nativeCheckInputs
      && pkg.pythonImportsCheck == [ "nixbench_report" ]
      && pkg.pytestFlagsArray == [ "tests" ]
    );
    "package-metadata" = passes (
      pkg.meta ? description && builtins.isString pkg.meta.description && pkg.meta.description != ""
      && pkg.meta ? homepage && builtins.isString pkg.meta.homepage && pkg.meta.homepage != ""
      && pkg.meta.license == lib.licenses.asl20
      && pkg.meta.mainProgram == "nixbench-report"
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"package-identity":false,"build-and-runtime-inputs":false,"test-contract":false,"package-metadata":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
