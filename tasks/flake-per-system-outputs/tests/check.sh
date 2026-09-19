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
  flakeAttempt = builtins.tryEval (import ${workdir}/flake.nix);
  flake = if flakeAttempt.success then flakeAttempt.value else {};
  outputsAttempt = builtins.tryEval (
    flake.outputs { self = outputsAttempt.value; }
  );
  outputs = if outputsAttempt.success then outputsAttempt.value else {};
  systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
  packageAndApp = system:
    let package = (builtins.getAttr system outputs.packages).default;
        app = (builtins.getAttr system outputs.apps).default;
    in package.type == "derivation"
      && package.pname == "nixbench-sample"
      && package.version == "0.1.0"
      && package.system == system
      && app.type == "app"
      && app.program == (toString package + "/bin/nixbench-sample")
      && app.meta.package == "nixbench-sample";
  checkAndShell = system:
    let package = (builtins.getAttr system outputs.packages).default;
        check = (builtins.getAttr system outputs.checks).eval;
        shell = (builtins.getAttr system outputs.devShells).default;
    in check == package && check.type == "derivation"
      && shell.type == "derivation" && shell.name == "nixbench-dev"
      && shell.system == system
      && builtins.elem "nixfmt" shell.tools && builtins.elem "statix" shell.tools;
in {
  schema_version = 2;
  criteria = {
    "systems-output" = passes (outputs.lib.systems == systems);
    "packages-and-apps" = passes (builtins.all packageAndApp systems);
    "checks-and-shells" = passes (builtins.all checkAndShell systems);
    "flake-evaluates" = passes (
      flakeAttempt.success
      && outputsAttempt.success
      && (flake.inputs or {}) == {}
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"systems-output":false,"packages-and-apps":false,"checks-and-shells":false,"flake-evaluates":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
