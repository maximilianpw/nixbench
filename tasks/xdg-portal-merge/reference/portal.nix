{
  config,
  lib,
  pkgs,
}:

let
  cfg = config.wayland.windowManager.hyprland;
  existingPortals = config.xdg.portal.extraPortals or [];
  existingConfigPackages = config.xdg.portal.configPackages or [];
  hyprlandPortal = pkgs.xdg-desktop-portal-hyprland;
  unique = list:
    builtins.attrValues (builtins.listToAttrs (map (value: {
        name = toString value;
        inherit value;
      })
      list));
in {
  xdg.portal = lib.mkIf cfg.enable {
    enable = true;
    extraPortals = unique (existingPortals ++ [ hyprlandPortal ]);
    configPackages = unique (existingConfigPackages ++ [ hyprlandPortal ]);
    config.common.default = [
      "hyprland"
      "gtk"
      "cosmic"
    ];
    config.hyprland.default = [
      "hyprland"
      "gtk"
    ];
  };
}
