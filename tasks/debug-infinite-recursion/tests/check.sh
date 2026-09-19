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
  lib.optionals = condition: values: if condition then values else [];
  explicitAttempt = builtins.tryEval (
    builtins.deepSeq (import ${workdir}/config.nix { inherit lib; })
      (import ${workdir}/config.nix { inherit lib; })
  );
  defaultAttempt = builtins.tryEval (
    builtins.deepSeq (import ${workdir}/config.nix {})
      (import ${workdir}/config.nix {})
  );
  withExplicitLib = if explicitAttempt.success then explicitAttempt.value else {};
  withDefaultLib = if defaultAttempt.success then defaultAttempt.value else {};
  expected = {
    name = "nixbench";
    enableDocs = true;
    outputs = [ "nixbench" "manual" ];
  };
in {
  schema_version = 2;
  criteria = {
    "evaluates-with-lib" = explicitAttempt.success;
    "evaluates-default-lib" = defaultAttempt.success;
    "expected-fields" = passes (
      (withDefaultLib.name or null) == "nixbench"
      && (withDefaultLib.enableDocs or null) == true
      && (withDefaultLib.outputs or null) == [ "nixbench" "manual" ]
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
if sed 's/[[:space:]]*#.*$//' "$workdir/config.nix" | grep -Eq 'lib[.]optionals'; then
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); p["criteria"]["evaluates-with-lib"]=False; json.dump(p,open(sys.argv[1],"w"),separators=(",",":"))' "$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
