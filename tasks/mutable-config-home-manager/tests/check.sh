#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  profile = import ${workdir}/profile.nix {
    profileDir = ".thunderbird/alice.default";
  };
  text = builtins.toJSON profile;
in
assert profile.programs.thunderbird.enable == true;
assert profile.home.sessionVariables.THUNDERBIRD_PROFILE_DIR == ".thunderbird/alice.default";
assert builtins.fromJSON profile.xdg.configFile."thunderbird/policies.json".text == {
  policies.DisableAppUpdate = true;
};
assert profile.mutableState == [ ".thunderbird/alice.default" ];
assert !(profile.home ? file);
assert builtins.match ".*profiles[.]ini.*" text == null;
assert builtins.match ".*prefs[.]js.*" text == null;
assert builtins.match ".*recursive.*" text == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
