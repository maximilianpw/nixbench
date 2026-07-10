# Compose Module Paths From Arguments

Edit `home.nix`.

The file receives module root paths through the `moduleRoots` argument:

```nix
{
  shared = ./modules/shared;
  config = ./dotfiles/config;
}
```

Return a Home Manager-style module attrset with:

- `imports` containing `tmux.nix`, `lsp.nix`, and `zsh.nix` under `moduleRoots.shared`, in that order.
- `home.file.".config/hypr/common.conf".source` pointing at `hypr/common.conf` under `moduleRoots.config`.
- `home.file.".config/hypr/keybind.conf".source` pointing at `hypr/keybind.conf` under `moduleRoots.config`.
- `passthru.importNames = [ "tmux" "lsp" "zsh" ]`.

Keep composed values as Nix paths, not strings. Use path addition with string suffixes such as `moduleRoots.shared + "/tmux.nix"`. Use parentheses around path additions inside lists. Do not use `{moduleRoots.config}/...`; Nix interpolation needs `${...}` in strings, but this task should keep path values instead of interpolated strings.
