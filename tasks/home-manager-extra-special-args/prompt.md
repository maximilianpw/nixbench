# Pass Flake Inputs Into Home Manager

Edit `flake.nix`.

The starter passes flake inputs to NixOS modules, but `home.nix` also expects the full `inputs` attrset so it can import Home Manager modules from flake inputs. Wire the flake so the Home Manager user module receives those inputs through the correct Home Manager mechanism.

Requirements:

- Keep the file as a flake with `outputs = inputs@{ nixpkgs, home-manager, ... }: ...`.
- Define `nixosConfigurations.nixbench = nixpkgs.lib.nixosSystem { ... };`.
- Keep `system = "x86_64-linux"`.
- Keep `specialArgs = { inherit inputs; };` for NixOS modules.
- Import `home-manager.nixosModules.home-manager` in the `modules` list.
- Set `home-manager.useGlobalPkgs = true`.
- Set `home-manager.useUserPackages = true`.
- Pass `inputs` into Home Manager with `home-manager.extraSpecialArgs = { inherit inputs; };`.
- Keep `home-manager.users.alice = import ./home.nix;`.
- Do not replace Home Manager with `home-manager.lib.homeManagerConfiguration`.

## Source Context

This task is modeled after NixOS Discourse threads where users passed `specialArgs` into `nixosSystem` and assumed Home Manager modules would receive the same flake inputs, leading to missing-argument or infinite-recursion errors until `home-manager.extraSpecialArgs` was used.

- NixOS Discourse: https://discourse.nixos.org/t/pass-specialargs-to-the-home-manager-module/33068
- NixOS Discourse: https://discourse.nixos.org/t/infinite-recursion-that-i-cannot-figure-out/71077
