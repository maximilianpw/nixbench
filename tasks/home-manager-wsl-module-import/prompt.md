# Import Home Manager As A NixOS Module On WSL

Edit `configuration.nix`.

The starter mixes Home Manager installation styles. Rewrite it as a NixOS module configuration for a NixOS-WSL host.

Requirements:

- Keep the file as a function accepting `homeManagerModule`.
- Import `homeManagerModule` through the top-level `imports` list.
- Set `wsl.enable = true`.
- Set `wsl.defaultUser = "nixos"`.
- Set `home-manager.useGlobalPkgs = true`.
- Set `home-manager.useUserPackages = true`.
- Configure `home-manager.users.nixos.programs.git.enable = true`.
- Do not use `<home-manager/nixos>`.
- Do not use `home-manager.lib.homeManagerConfiguration`; that is the standalone Home Manager entrypoint, not the NixOS module import.

## Source Context

This task is modeled after a NixOS Discourse thread where a user could not get Home Manager working inside NixOS-WSL and said Google and ChatGPT were of no use.

- NixOS Discourse: https://discourse.nixos.org/t/cant-enable-home-manager-in-wsl-nixos/49364
