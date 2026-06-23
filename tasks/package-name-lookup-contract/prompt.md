# Use Existing Package Names

Edit `packages.nix`.

Return a NixOS-style module that sets `environment.systemPackages` to these packages from the provided `pkgs` set:

- `git`
- `ripgrep`
- `fd`
- `bat`
- `eza`
- `nixfmt-rfc-style`
- `nil`
- `statix`
- `deadnix`

Use the exact attributes above. Do not invent package names or use older replacement names such as `exa`, `nixfmt`, or `nix-language-server`.

## Source Context

This task is modeled after reports that LLMs make up Nix packages or suggest package names/options that do not exist without a live Nix search source.

- Reddit: https://www.reddit.com/r/NixOS/comments/1rqy6h0/nixos_migration_was_relatively_easy_using_llm/
- Reddit: https://www.reddit.com/r/NixOS/comments/1n6er8g/nixos_for_a_beginner_in_2025/
