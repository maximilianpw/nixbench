# Manage Home Files Declaratively

Edit `home.nix`.

The starter uses an imperative activation script to create user directories and write a config file. Rewrite it using Home Manager's declarative file and XDG options.

Requirements:

- Keep the file as a function accepting `homeDirectory` and `configText`.
- Enable `xdg.userDirs`.
- Set `xdg.userDirs.createDirectories = true`.
- Set `xdg.userDirs.documents = "${homeDirectory}/Documents"`.
- Set `xdg.userDirs.download = "${homeDirectory}/Downloads"`.
- Write `configText` to `xdg.configFile."nixbench/app.toml".text`.
- Create a placeholder at `home.file."GitHub_Repos/.keep".text`.
- Do not use `home.activation`, `mkdir`, `ln -s`, or symlink farms.

## Source Context

This task is modeled after user reports where ChatGPT gave wrong or imperative answers for creating home folders or putting files under `$HOME/.config`, while community answers pointed toward Home Manager XDG and file options.

- Reddit: https://www.reddit.com/r/NixOS/comments/175a3e6/is_it_right_chatgpt_how_to_create_the_documents/
- NixOS Discourse: https://discourse.nixos.org/t/download-config-files-to-home-dir/60934
