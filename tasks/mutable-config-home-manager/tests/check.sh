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
  hasPrefix = prefix: value:
    builtins.isString value
    && builtins.substring 0 (builtins.stringLength prefix) value == prefix;
  profileChecks = profileDir:
    let
      profile = import ${workdir}/profile.nix { inherit profileDir; };
      homeFiles = get [ "home" "file" ] {} profile;
      fileNames = if builtins.isAttrs homeFiles then builtins.attrNames homeFiles else [];
      definitionPaths = definition:
        (if builtins.isAttrs definition && definition ? target && builtins.isString definition.target then [ definition.target ] else [])
        ++ (
          if builtins.isAttrs definition && definition ? source
            && (builtins.isString definition.source || builtins.typeOf definition.source == "path")
          then [ toString definition.source ]
          else []
        );
      managedPaths = fileNames ++ builtins.concatLists (
        map definitionPaths (if builtins.isAttrs homeFiles then builtins.attrValues homeFiles else [])
      );
      thunderbirdRoot = if builtins.isAttrs homeFiles then homeFiles.".thunderbird" or {} else {};
      managesMutableProfile = name:
        name == profileDir || hasPrefix "\${profileDir}/" name;
      managesForbiddenFile = name:
        hasPrefix ".thunderbird/" name
        && (
          builtins.match ".*profiles[.]ini.*" name != null
          || builtins.match ".*prefs[.]js.*" name != null
        );
      policyText = get [ "xdg" "configFile" "thunderbird/policies.json" "text" ] null profile;
      parsedPolicy =
        if builtins.isString policyText
        then builtins.tryEval (builtins.fromJSON policyText)
        else { success = false; value = {}; };
      policies = if parsedPolicy.success && builtins.isAttrs parsedPolicy.value then parsedPolicy.value else {};
    in {
      thunderbird = get [ "programs" "thunderbird" "enable" ] false profile == true;
      variable = get [ "home" "sessionVariables" "THUNDERBIRD_PROFILE_DIR" ] null profile == profileDir;
      policy = get [ "policies" "DisableAppUpdate" ] false policies == true;
      boundary =
        get [ "mutableState" ] null profile == [ profileDir ]
        && builtins.all (path: !(managesMutableProfile path)) managedPaths
        && builtins.all (path: !(managesForbiddenFile path)) managedPaths
        && !(get [ "recursive" ] false thunderbirdRoot);
    };
  alice = profileChecks ".thunderbird/alice.default";
  bob = profileChecks ".thunderbird/bob.default";
in {
  schema_version = 2;
  criteria = {
    "thunderbird-config" = passes (alice.thunderbird && bob.thunderbird);
    "profile-variable" = passes (alice.variable && bob.variable);
    "managed-policy" = passes (alice.policy && bob.policy);
    "mutable-state-boundary" = passes (alice.boundary && bob.boundary);
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"thunderbird-config":false,"profile-variable":false,"managed-policy":false,"mutable-state-boundary":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
