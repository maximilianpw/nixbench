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
    extraPortals = [
      pkgs.xdg-desktop-portal-hyprland
    ];
    configPackages = [
      pkgs.xdg-desktop-portal-hyprland
    ];
    config.common.default = [
      "hyprland"
    ];
  };
}
