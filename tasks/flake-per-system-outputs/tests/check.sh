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
  get = path: default: value:
    if path == [] then value
    else if builtins.isAttrs value && builtins.hasAttr (builtins.head path) value
    then get (builtins.tail path) default (builtins.getAttr (builtins.head path) value)
    else default;
  flakeAttempt = builtins.tryEval (import ${workdir}/flake.nix);
  flake = if flakeAttempt.success then flakeAttempt.value else {};
  outputsFunction = get [ "outputs" ] null flake;
  outputsAttempt = builtins.tryEval (
    if builtins.isFunction outputsFunction
    then outputsFunction { self = outputsAttempt.value; }
    else {}
  );
  outputs = if outputsAttempt.success then outputsAttempt.value else {};
  systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
  packageAndApp = system:
    let package = get [ "packages" system "default" ] {} outputs;
        app = get [ "apps" system "default" ] {} outputs;
    in get [ "type" ] null package == "derivation"
      && get [ "pname" ] null package == "nixbench-sample"
      && get [ "version" ] null package == "0.1.0"
      && get [ "system" ] null package == system
      && get [ "type" ] null app == "app"
      && get [ "program" ] null app == (toString package + "/bin/nixbench-sample")
      && get [ "meta" "package" ] null app == "nixbench-sample";
  checkAndShell = system:
    let package = get [ "packages" system "default" ] {} outputs;
        check = get [ "checks" system "eval" ] null outputs;
        shell = get [ "devShells" system "default" ] {} outputs;
    in check == package && get [ "type" ] null check == "derivation"
      && get [ "type" ] null shell == "derivation"
      && get [ "name" ] null shell == "nixbench-dev"
      && get [ "system" ] null shell == system
      && builtins.elem "nixfmt" (get [ "tools" ] [] shell)
      && builtins.elem "statix" (get [ "tools" ] [] shell);
in {
  schema_version = 2;
  criteria = {
    "systems-output" = passes (get [ "lib" "systems" ] null outputs == systems);
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
