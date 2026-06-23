{ inputs, pkgs }:
{
  environment.systemPackages = [
    pkgs.mangohud
    "${inputs.legacylauncher.packages.${pkgs.system}.default}"
    pkgs.libreoffice-fresh
  ];
}
