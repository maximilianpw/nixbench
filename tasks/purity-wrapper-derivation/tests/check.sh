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
  stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
  lib = {
    makeBinPath = paths:
      if paths == [ coreutils ]
      then "/nix/store/nixbench-coreutils-path/bin"
      else throw "makeBinPath must receive only coreutils";
  };
  makeWrapper = "makeWrapper";
  coreutils = "/nix/store/coreutils";
  bash = {
    outPath = "/nix/store/nixbench-bash-sentinel";
    __toString = self: self.outPath;
    marker = 199;
  };
  drv = import ${workdir}/derivation.nix {
    inherit stdenv lib makeWrapper coreutils bash;
  };
in {
  schema_version = 2;
  criteria = {
    "derivation-identity" = passes (
      drv.__mkDerivation == true && drv.pname == "pure-runner" && drv.version == "1.0.0"
    );
    "wrapper-inputs" = passes (
      builtins.elem makeWrapper drv.nativeBuildInputs
      && builtins.match ".*makeWrapper.*/nix/store/nixbench-bash-sentinel/bin/bash.*" drv.installPhase != null
      && builtins.match ".*nixbench-coreutils-path/bin.*" drv.installPhase != null
    );
    "pure-install-phase" = passes (
      builtins.match ".*usr/bin.*" drv.installPhase == null
      && builtins.match ".*HOME.*" drv.installPhase == null
    );
    "purity-marker" = passes (drv.passthru.pure == true);
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"derivation-identity":false,"wrapper-inputs":false,"pure-install-phase":false,"purity-marker":false},"notes":[]}' >"$score_tmp"
fi
if sed 's/[[:space:]]*#.*$//' "$workdir/derivation.nix" | grep -Eq "builtins[.]getEnv|lib[.]getExe|[\"']/usr/bin|[\"']/bin|\\\$HOME"; then
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); p["criteria"]["pure-install-phase"]=False; json.dump(p,open(sys.argv[1],"w"),separators=(",",":"))' "$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
