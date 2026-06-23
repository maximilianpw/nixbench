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

  xdg.configFile."nixbench/app.toml".text = configText;

  home.file."GitHub_Repos/.keep".text = "";
}
