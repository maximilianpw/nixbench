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
  report = import ${workdir}/report.nix;
  text = builtins.toJSON report;
  analysisText = builtins.toJSON report.analysis;
in {
  schema_version = 2;
  criteria = {
    "report-fields" = passes (
      builtins.isString (get [ "title" ] null report) && get [ "title" ] "" report != ""
      && get [ "failureClass" ] null report == "evaluation"
      && builtins.isString (get [ "expected" ] null report) && get [ "expected" ] "" report != ""
      && builtins.isString (get [ "actual" ] null report) && get [ "actual" ] "" report != ""
    );
    "reproduction-and-system" = passes (
      report.system.system == "x86_64-linux"
      && report.system.nixosRelease == "25.05"
      && report.system.nixpkgsRevision == "8f3b2d1"
      && builtins.elem "nixos-rebuild test --flake .#workstation" report.reproduction
    );
    "outcome-evidence" = passes (
      report.expectedStatus == "evaluation-succeeds"
      && report.actualStatus == "evaluation-fails"
      && builtins.isList report.logs
      && builtins.length report.logs > 0
      && builtins.all (item: builtins.isString item && item != "") report.logs
      && builtins.elem "error: The option services.xserver.displayManager.sddm.enable does not exist" report.logs
    );
    "bounded-analysis" = passes (
      builtins.isAttrs report.analysis
      && builtins.isList report.analysis.observed
      && builtins.length report.analysis.observed > 0
      && builtins.all (item: builtins.isString item && item != "") report.analysis.observed
      && builtins.isString report.analysis.likelyFix
      && report.analysis.likelyFix != ""
      && builtins.isList report.analysis.unverified
      && builtins.match ".*services[.]xserver[.]displayManager[.]sddm[.]enable.*" analysisText != null
      && builtins.match ".*services[.]displayManager[.]sddm[.]enable.*" analysisText != null
      && !(report.analysis ? rootCause)
      && !(report.analysis ? confirmedRootCause)
      && report.confidence == "observed"
      && builtins.match ".*[Cc][Hh][Aa][Tt][Gg][Pp][Tt].*" text == null
      && builtins.match ".*[Cc][Oo][Pp][Ii][Ll][Oo][Tt].*" text == null
      && builtins.match ".*[^A-Za-z][Aa][Ii][^A-Za-z].*" text == null
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"report-fields":false,"reproduction-and-system":false,"outcome-evidence":false,"bounded-analysis":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
