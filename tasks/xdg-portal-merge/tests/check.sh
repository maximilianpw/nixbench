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
  pkgs = {
    xdg-desktop-portal-hyprland = "/nix/store/xdg-desktop-portal-hyprland";
    xdg-desktop-portal-gtk = "/nix/store/xdg-desktop-portal-gtk";
    xdg-desktop-portal-cosmic = "/nix/store/xdg-desktop-portal-cosmic";
    cosmic-session = "/nix/store/cosmic-session";
  };
  config = {
    wayland.windowManager.hyprland.enable = true;
    xdg.portal.extraPortals = [
      pkgs.xdg-desktop-portal-cosmic
      pkgs.xdg-desktop-portal-gtk
    ];
    xdg.portal.configPackages = [
      pkgs.cosmic-session
    ];
  };
  module = import ${workdir}/portal.nix { inherit config lib pkgs; };
  portal = module.xdg.portal;
in
assert portal.__mkIf == true;
assert portal.content.enable == true;
assert builtins.elem pkgs.xdg-desktop-portal-hyprland portal.content.extraPortals;
assert builtins.elem pkgs.xdg-desktop-portal-cosmic portal.content.extraPortals;
assert builtins.elem pkgs.xdg-desktop-portal-gtk portal.content.extraPortals;
assert builtins.elem pkgs.xdg-desktop-portal-hyprland portal.content.configPackages;
assert builtins.elem pkgs.cosmic-session portal.content.configPackages;
assert portal.content.config.common.default != [ "hyprland" ];
assert builtins.elem "hyprland" portal.content.config.common.default;
assert builtins.elem "gtk" portal.content.config.common.default;
assert builtins.elem "cosmic" portal.content.config.common.default;
assert portal.content.config.hyprland.default == [ "hyprland" "gtk" ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
