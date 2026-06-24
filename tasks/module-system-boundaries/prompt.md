# Respect NixOS, Home Manager, And nix-darwin Boundaries

Edit `shared.nix`.

The starter reuses one module across incompatible module systems. Rewrite it to expose plain shared data plus separate modules for NixOS, Home Manager, and nix-darwin.

Requirements:

- Return an attrset containing `shared`, `nixosModule`, `homeManagerModule`, and `darwinModule`.
- `shared.packages` must contain `pkgs.ripgrep` and `pkgs.fd`.
- `shared.shell` must be `"fish"`.
- `nixosModule` must set `programs.fish.enable = true` and `environment.systemPackages = shared.packages`.
- `homeManagerModule` must set `programs.fish.enable = true` and `home.packages = shared.packages`.
- `darwinModule` must set `programs.fish.enable = true` and `environment.systemPackages = shared.packages`.
- Do not set `home.*` options in the NixOS or nix-darwin modules.
- Do not set `environment.*` options in the Home Manager module.

## Source Context

This task is modeled after reports and discussions where NixOS, Home Manager, and nix-darwin module systems were blurred together. The correct approach is to share plain values or helper functions while keeping module outputs separate for each module system.

- Reddit: https://www.reddit.com/r/NixOS/comments/1gwgzbd/nixos_on_macos_nix_not_picking_up/
- Reddit: https://www.reddit.com/r/NixOS/comments/1rsassa/welcome_to_den_v0120/
