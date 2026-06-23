# Development Shell Tooling Contract

Edit `shell.nix`.

Create a development shell using `mkShell`.

Requirements:

- `name = "nixbench-dev"`.
- Include `nixfmt-rfc-style`, `statix`, `deadnix`, and `nil` in `packages`.
- Include `alejandra` only when the argument is not `null`.
- Set `NIXBENCH_FORMATTER = "nixfmt-rfc-style"`.
- Add a `shellHook` that enables `nix-command` and `flakes` through `NIX_CONFIG`.
