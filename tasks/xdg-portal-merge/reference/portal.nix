{
  config,
  lib,
  pkgs,
  ...
}:

let
  cfg = config.wayland.windowManager.hyprland;
  hyprlandPortal = pkgs.xdg-desktop-portal-hyprland;
in {
  xdg.portal = lib.mkIf cfg.enable {
    enable = true;
    extraPortals = lib.mkAfter [ hyprlandPortal ];
    configPackages = lib.mkAfter [ hyprlandPortal ];
    config.common.default = lib.mkAfter [
      "hyprland"
      "gtk"
    ];
  };
}
