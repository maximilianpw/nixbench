{
  config,
  lib,
  pkgs,
}:

let
  cfg = config.wayland.windowManager.hyprland;
in {
  xdg.portal = lib.mkIf cfg.enable {
    enable = true;
    extraPortals = lib.mkForce [
      pkgs.xdg-desktop-portal-hyprland
    ];
    configPackages = lib.mkForce [
      pkgs.xdg-desktop-portal-hyprland
    ];
    config.common.default = lib.mkForce [
      "hyprland"
    ];
  };
}
