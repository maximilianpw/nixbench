{ pkgs }:
{
  environment.systemPackages = [
    pkgs.git
    pkgs.ripgrep
    pkgs.fd
    pkgs.bat
    pkgs.eza
    pkgs.nixfmt-rfc-style
    pkgs.nil
    pkgs.statix
    pkgs.deadnix
  ];
}
