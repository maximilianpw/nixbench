{ inputs, pkgs }:
{
  environment.systemPackages = [
    (if pkgs.system == "x86_64-linux" then pkgs.libreoffice-fresh else pkgs.mangohud)
    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher
    pkgs.libreoffice-fresh
  ];
}
