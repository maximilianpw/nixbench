# Merge XDG Portal Configuration

Edit `portal.nix`.

The starter models a Home Manager-style Hyprland module that writes portal configuration as if Hyprland were the only desktop environment. That can hide existing system portal configuration for other desktops and applications.

Rewrite the module fragment so that:

- It still enables portal support when `wayland.windowManager.hyprland.enable` is true.
- It includes `pkgs.xdg-desktop-portal-hyprland`.
- It preserves existing `config.xdg.portal.extraPortals`.
- It preserves existing `config.xdg.portal.configPackages`.
- The merged defaults include both Hyprland and non-Hyprland fallbacks.
- It does not replace the existing portal package lists with Hyprland-only lists.

Do not solve this by disabling portals or by assuming the user only runs Hyprland.

## Source Context

This task is modeled after reports that Home Manager-generated portal configuration for Hyprland can break portal discovery for other environments and applications:

- NixOS Discourse: https://discourse.nixos.org/t/hyprland-home-manager-module-breaks-portal-discovery-for-other-desktop-environments/78042
- GitHub: https://github.com/nix-community/home-manager/issues/9201
