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
  hasPrefix = prefix: value:
    builtins.substring 0 (builtins.stringLength prefix) value == prefix;
  profileChecks = profileDir:
    let
      profile = import ${workdir}/profile.nix { inherit profileDir; };
      homeFiles = profile.home.file or {};
      fileNames = builtins.attrNames homeFiles;
      definitionPaths = definition:
        (if definition ? target && builtins.isString definition.target then [ definition.target ] else [])
        ++ (
          if definition ? source
            && (builtins.isString definition.source || builtins.typeOf definition.source == "path")
          then [ toString definition.source ]
          else []
        );
      managedPaths = fileNames ++ builtins.concatLists (
        map definitionPaths (builtins.attrValues homeFiles)
      );
      thunderbirdRoot = homeFiles.".thunderbird" or {};
      managesMutableProfile = name:
        name == profileDir || hasPrefix "\${profileDir}/" name;
      managesForbiddenFile = name:
        hasPrefix ".thunderbird/" name
        && (
          builtins.match ".*profiles[.]ini.*" name != null
          || builtins.match ".*prefs[.]js.*" name != null
        );
      policies = builtins.fromJSON profile.xdg.configFile."thunderbird/policies.json".text;
    in {
      thunderbird = profile.programs.thunderbird.enable == true;
      variable = profile.home.sessionVariables.THUNDERBIRD_PROFILE_DIR == profileDir;
      policy = policies.policies.DisableAppUpdate == true;
      boundary =
        profile.mutableState == [ profileDir ]
        && builtins.all (path: !(managesMutableProfile path)) managedPaths
        && builtins.all (path: !(managesForbiddenFile path)) managedPaths
        && !(thunderbirdRoot.recursive or false);
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
