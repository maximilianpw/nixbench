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
  system = get [ "system" ] {} report;
  reproduction = get [ "reproduction" ] [] report;
  logs = get [ "logs" ] [] report;
  analysis = get [ "analysis" ] {} report;
  observed = get [ "observed" ] [] analysis;
  unverified = get [ "unverified" ] [] analysis;
  analysisText = builtins.toJSON analysis;
  text = builtins.toJSON report;
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
      get [ "system" ] null system == "x86_64-linux"
      && get [ "nixosRelease" ] null system == "25.05"
      && get [ "nixpkgsRevision" ] null system == "8f3b2d1"
      && builtins.isList reproduction
      && builtins.elem "nixos-rebuild test --flake .#workstation" reproduction
    );
    "outcome-evidence" = passes (
      get [ "expectedStatus" ] null report == "evaluation-succeeds"
      && get [ "actualStatus" ] null report == "evaluation-fails"
      && builtins.isList logs
      && builtins.length logs > 0
      && builtins.all (item: builtins.isString item && item != "") logs
      && builtins.elem "error: The option services.xserver.displayManager.sddm.enable does not exist" logs
    );
    "bounded-analysis" = passes (
      builtins.isAttrs analysis
      && builtins.isList observed
      && builtins.length observed > 0
      && builtins.all (item: builtins.isString item && item != "") observed
      && builtins.isString (get [ "likelyFix" ] null analysis)
      && get [ "likelyFix" ] "" analysis != ""
      && builtins.isList unverified
      && builtins.match ".*services[.]xserver[.]displayManager[.]sddm[.]enable.*" analysisText != null
      && builtins.match ".*services[.]displayManager[.]sddm[.]enable.*" analysisText != null
      && !(analysis ? rootCause)
      && !(analysis ? confirmedRootCause)
      && get [ "confidence" ] null report == "observed"
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
