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
  makePackage = name: { __package = name; };
  pkgs = {
    alsa-lib = makePackage "alsa-lib";
    glib = makePackage "glib";
    gtk3 = makePackage "gtk3";
  };
  result = import ${workdir}/wrapper.nix {
    inherit appimageTools buildFHSUserEnv fetchurl pkgs;
  };
  fhsPackages = result.fhsEnv.targetPkgs pkgs;
  requiredFhsPackages = [ pkgs.alsa-lib pkgs.glib pkgs.gtk3 ];
in
assert result.appimage.__appimage == "wrapType2";
assert result.appimage.pname == "vendor-tool";
assert result.appimage.version == "2.0.0";
assert result.appimage.src.__fetcher == "url";
assert builtins.isString result.appimage.src.url;
assert builtins.match "https?://.+" result.appimage.src.url != null;
assert builtins.isString result.appimage.src.hash;
assert builtins.match "sha256-[A-Za-z0-9+/]{43}=" result.appimage.src.hash != null;
assert result.fhsEnv.__fhs == true;
assert result.fhsEnv.name == "vendor-tool-fhs";
assert builtins.all (package: builtins.elem package fhsPackages) requiredFhsPackages;
assert result.fhsEnv.runScript == "vendor-tool";
assert builtins.attrNames result == [ "appimage" "fhsEnv" ];
assert !(result.appimage ? activation);
assert !(result.fhsEnv ? activation);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
