# Select The Right Flake Package Output

Edit `packages.nix`.

The starter assumes every flake exposes `packages.${system}.default` and stringifies the result. Fix it to use the actual package output from the provided flake input.

Requirements:

- Keep the file as a function accepting `inputs` and `pkgs`.
- Select `inputs.legacylauncher.packages.${pkgs.system}.legacylauncher`.
- Put that package value in `environment.systemPackages`.
- Do not use `.default`.
- Do not convert the package to a string with interpolation.
- Also include `pkgs.mangohud` and `pkgs.libreoffice-fresh`.

## Source Context

This task is modeled after a NixOS Discourse thread where a user and ChatGPT were stuck on `attribute 'default' missing` from a flake package output.

- NixOS Discourse: https://discourse.nixos.org/t/error-attribute-default-missing/59474
