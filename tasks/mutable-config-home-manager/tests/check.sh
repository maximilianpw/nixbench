#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  hasPrefix = prefix: value:
    builtins.substring 0 (builtins.stringLength prefix) value == prefix;
  checkProfile = profileDir:
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
    in
      profile.programs.thunderbird.enable == true
      && profile.home.sessionVariables.THUNDERBIRD_PROFILE_DIR == profileDir
      && policies.policies.DisableAppUpdate == true
      && profile.mutableState == [ profileDir ]
      && builtins.all (path: !(managesMutableProfile path)) managedPaths
      && builtins.all (path: !(managesForbiddenFile path)) managedPaths
      && !(thunderbirdRoot.recursive or false);
in
assert checkProfile ".thunderbird/alice.default";
assert checkProfile ".thunderbird/bob.default";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
