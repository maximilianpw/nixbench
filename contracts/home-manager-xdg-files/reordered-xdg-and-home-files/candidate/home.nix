{
  homeDirectory ? "/home/alice",
  configText ? "theme = \"dark\"\n",
}:
{
  xdg.userDirs = {
    enable = true;
    createDirectories = true;
    documents = "${homeDirectory}/Documents";
    download = "${homeDirectory}/Downloads";
  };

  home.file."GitHub_Repos/.keep".text = "";

  xdg.configFile."nixbench/app.toml".text = configText;
}
