{ inputs, pkgs }:
{
  environment.systemPackages = [
    (if pkgs.system == "aarch64-darwin" then pkgs.libreoffice-fresh else pkgs.mangohud)
    inputs.legacylauncher.packages.${pkgs.system}.legacylauncher
    pkgs.libreoffice-fresh
  ];
}
