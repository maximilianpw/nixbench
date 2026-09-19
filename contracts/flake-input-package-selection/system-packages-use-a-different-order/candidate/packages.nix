{ inputs, pkgs }:
{
  environment.systemPackages = [
    pkgs.libreoffice-fresh
    pkgs.mangohud
    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher
  ];
}
