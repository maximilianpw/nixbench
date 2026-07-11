#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.mkIf = condition: content: {
    __mkIf = condition;
    inherit content;
  };
  lib.mkAfter = content: content;
  lib.mkDefault = content: content;
  pkgs = {
    xdg-desktop-portal-hyprland = "/nix/store/xdg-desktop-portal-hyprland";
  };
  evaluate = enabled: import ${workdir}/portal.nix {
    config = {
      wayland.windowManager.hyprland.enable = enabled;
      xdg.portal.extraPortals = throw "do not read an option while defining it";
      xdg.portal.configPackages = throw "do not read an option while defining it";
    };
    inherit lib pkgs;
  };
  portal = (evaluate true).xdg.portal;
  disabledPortal = (evaluate false).xdg.portal;
  existingPortals = [
    "/nix/store/existing-cosmic-portal"
    "/nix/store/existing-gtk-portal"
  ];
  existingConfigPackages = [
    "/nix/store/existing-cosmic-session"
  ];
  existingDefaults = [];
  commonDefaults = portal.content.config.common.default or [];
  hyprlandDefaults = portal.content.config.hyprland.default or [];
  mergedPortals = existingPortals ++ portal.content.extraPortals;
  mergedConfigPackages = existingConfigPackages ++ portal.content.configPackages;
  mergedDefaults = existingDefaults ++ commonDefaults ++ hyprlandDefaults;
in
assert portal.__mkIf == true;
assert disabledPortal.__mkIf == false;
assert portal.content.enable == true;
assert builtins.elem pkgs.xdg-desktop-portal-hyprland mergedPortals;
assert builtins.elem "/nix/store/existing-cosmic-portal" mergedPortals;
assert builtins.elem "/nix/store/existing-gtk-portal" mergedPortals;
assert builtins.elem pkgs.xdg-desktop-portal-hyprland mergedConfigPackages;
assert builtins.elem "/nix/store/existing-cosmic-session" mergedConfigPackages;
assert builtins.elem "hyprland" mergedDefaults;
assert builtins.any (fallback: fallback != "hyprland") mergedDefaults;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
