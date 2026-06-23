{ inputs, pkgs }:
{
  environment.systemPackages = [
    pkgs.mangohud
    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher
    pkgs.libreoffice-fresh
  ];
}
