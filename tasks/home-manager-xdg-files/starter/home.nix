{
  homeDirectory ? "/home/alice",
  configText ? "theme = \"dark\"\n",
}:
{
  home.activation.createFolders = ''
    mkdir -p ${homeDirectory}/Documents
    mkdir -p ${homeDirectory}/Downloads
    mkdir -p ${homeDirectory}/.config/nixbench
    printf %s '${configText}' > ${homeDirectory}/.config/nixbench/app.toml
    mkdir -p ${homeDirectory}/GitHub_Repos
  '';
}
