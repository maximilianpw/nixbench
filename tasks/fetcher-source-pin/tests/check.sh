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
  fetchFromGitHub = attrs: attrs // { __fetcher = "github"; };
  src = import ${workdir}/source.nix { inherit fetchFromGitHub; };
in {
  schema_version = 2;
  criteria = {
    "github-source" = passes (src.__fetcher == "github");
    "repository-identity" = passes (
      src.owner == "nix-community" && src.repo == "nixbench-fixture"
    );
    "pinned-revision-hash" = passes (
      builtins.match "[0-9a-f]{40}" src.rev != null
      && builtins.isString src.hash
      && builtins.match "sha256-[A-Za-z0-9+/]{43}=" src.hash != null
    );
    "fetch-options" = passes (
      src.fetchSubmodules == true && src.leaveDotGit == false
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"github-source":false,"repository-identity":false,"pinned-revision-hash":false,"fetch-options":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
