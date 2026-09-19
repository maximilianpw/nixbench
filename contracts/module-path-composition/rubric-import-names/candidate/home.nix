{ moduleRoots, ... }:
let common = moduleRoots.config + "/hypr/common.conf"; keybind = moduleRoots.config + "/hypr/keybind.conf"; in { imports = map (name: moduleRoots.shared + ("/" + name + ".nix")) [ "tmux" "lsp" "zsh" ]; home.file = { ".config/hypr/common.conf".source = common; ".config/hypr/keybind.conf".source = keybind; }; passthru.importNames = [ "tmux" "lsp" "zsh" ]; }
