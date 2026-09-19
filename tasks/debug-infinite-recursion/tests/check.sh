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
  lib.optional = condition: value: if condition then [ value ] else [];
  withExplicitLib = import ${workdir}/config.nix { inherit lib; };
  withDefaultLib = import ${workdir}/config.nix {};
  expected = {
    name = "nixbench";
    enableDocs = true;
    outputs = [ "nixbench" "manual" ];
  };
in {
  schema_version = 2;
  criteria = {
    "evaluates-with-lib" = passes (withExplicitLib == expected);
    "evaluates-default-lib" = passes (withDefaultLib == expected);
    "expected-fields" = passes (
      withDefaultLib.name == "nixbench"
      && withDefaultLib.enableDocs == true
      && withDefaultLib.outputs == [ "nixbench" "manual" ]
    );
    "exact-output-shape" = passes (
      builtins.attrNames withDefaultLib == [ "enableDocs" "name" "outputs" ]
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"evaluates-with-lib":false,"evaluates-default-lib":false,"expected-fields":false,"exact-output-shape":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
