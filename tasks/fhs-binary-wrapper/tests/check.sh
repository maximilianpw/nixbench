#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  appimageTools.wrapType2 = attrs: attrs // { __appimage = "wrapType2"; };
  buildFHSUserEnv = attrs: attrs // { __fhs = true; };
  fetchurl = attrs: attrs // { __fetcher = "url"; };
  pkgs = {
    alsa-lib = "alsa-lib";
    glib = "glib";
    gtk3 = "gtk3";
  };
  result = import ${workdir}/wrapper.nix {
    inherit appimageTools buildFHSUserEnv fetchurl pkgs;
  };
  fhsPackages = result.fhsEnv.targetPkgs pkgs;
in
assert result.appimage.__appimage == "wrapType2";
assert result.appimage.pname == "vendor-tool";
assert result.appimage.version == "2.0.0";
assert result.appimage.src.__fetcher == "url";
assert result.fhsEnv.__fhs == true;
assert result.fhsEnv.name == "vendor-tool-fhs";
assert fhsPackages == [ pkgs.alsa-lib pkgs.glib pkgs.gtk3 ];
assert result.fhsEnv.runScript == "vendor-tool";
assert !(result ? environment);
assert !(result ? system);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
