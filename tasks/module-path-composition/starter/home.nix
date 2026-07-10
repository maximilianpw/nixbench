{moduleRoots, ...}: {
  imports = [
    moduleRoots.shared + ./tmux.nix
    moduleRoots.shared + ./lsp.nix
  ];

  home.file.".config/hypr/common.conf".source = {moduleRoots.config}/hypr/common.conf;
}
