{moduleRoots, ...}: {
  imports = [
    (moduleRoots.shared + "/tmux.nix")
    (moduleRoots.shared + "/lsp.nix")
    (moduleRoots.shared + "/zsh.nix")
  ];

  home.file = {
    ".config/hypr/common.conf".source = moduleRoots.config + "/hypr/common.conf";
    ".config/hypr/keybind.conf".source = moduleRoots.config + "/hypr/keybind.conf";
  };

  passthru.importNames = ["tmux" "lsp" "zsh"];
}
