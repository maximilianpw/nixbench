# Wire Command-Not-Found Into Nushell

Edit `module.nix`.

The starter only wires command-not-found support into Bash. Extend the module fragment so Nushell users get equivalent missing-command suggestions when both `programs.command-not-found.enable` and `programs.nushell.enable` are true.

Requirements:

- Keep the existing Bash initialization behavior.
- Add a Nushell hook through `programs.nushell.extraConfig`.
- The Nushell hook must call the command-not-found executable from `pkgs.nix-index`.
- Include `pkgs.nix-index` in `environment.systemPackages` so the hook target is present.
- Gate the generated config with `lib.mkIf`; do not enable Nushell or command-not-found unconditionally.
- The hook text must use Nushell's `hooks.command_not_found` configuration path.

Do not replace the Bash setup with a Bash-specific snippet inside Nushell config.

## Source Context

This task is modeled after an open nixpkgs issue reporting that `programs.command-not-found.enable` works in Bash but not in Nushell:

- GitHub: https://github.com/NixOS/nixpkgs/issues/532042
