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
  makePkg = attrs: attrs // {
    __overrideCount = attrs.__overrideCount or 0;
    overrideAttrs = f:
      let
        next = attrs // f attrs;
      in
      makePkg (next // {
        __overrideCount = (attrs.__overrideCount or 0) + 1;
      });
  };
  overlay = import ${workdir}/overlay.nix;
  base = {
    tinygrep = makePkg {
      pname = "tinygrep";
      version = "0.1.0";
      patches = [ ./existing.patch ];
      doCheck = false;
      meta = {
        description = "tiny grep";
        homepage = "https://example.invalid/tinygrep";
        broken = true;
      };
    };
  };
  final = base // result // {
    tinygrep = makePkg (result.tinygrep // { __fromFinal = 151; });
  };
  result = overlay final base;
in {
  schema_version = 2;
  criteria = {
    "base-override" = passes (
      result.tinygrep.version == "0.2.0" && result.tinygrep.__overrideCount == 1
    );
    "patch-and-check" = passes (
      result.tinygrep.doCheck == true
      && result.tinygrep.patches == [ ./existing.patch ${workdir}/fix-musl.patch ]
    );
    "meta-preservation" = passes (
      result.tinygrep.meta.description == "tiny grep"
      && result.tinygrep.meta.homepage == "https://example.invalid/tinygrep"
      && result.tinygrep.meta.broken == false
    );
    "debug-from-final" = passes (
      result.tinygrep-debug.pname == "tinygrep-debug"
      && result.tinygrep-debug.version == "0.2.0"
      && result.tinygrep-debug.dontStrip == true
      && result.tinygrep-debug.patches == result.tinygrep.patches
      && result.tinygrep-debug.doCheck == result.tinygrep.doCheck
      && result.tinygrep-debug.meta == result.tinygrep.meta
      && result.tinygrep-debug.__overrideCount == 2
      && result.tinygrep-debug.__fromFinal == 151
    );
  };
  notes = [];
}
EOF

touch "$tmpdir/existing.patch"
score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"base-override":false,"patch-and-check":false,"meta-preservation":false,"debug-from-final":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
