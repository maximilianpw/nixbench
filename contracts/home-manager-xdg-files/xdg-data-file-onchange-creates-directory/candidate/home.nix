{ homeDirectory ? "/home/alice", configText ? "theme = \"dark\"\n" }:
{
  xdg.userDirs = { enable = true; createDirectories = true; documents = "${homeDirectory}/Documents"; download = "${homeDirectory}/Downloads"; };
  xdg.configFile."nixbench/app.toml".text = configText;
  xdg.dataFile."nixbench/state" = { text = "managed"; onChange = ''mkdir -p "${homeDirectory}/.local/share/nixbench"''; };
  home.file."GitHub_Repos/.keep".text = "";
}
