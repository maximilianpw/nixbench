{ pkgs }:
{
  environment.systemPackages = [
    pkgs.git
    pkgs.ripgrep
    pkgs.fd
    pkgs.eza
    pkgs.nixfmt-rfc-style
    pkgs.nil
    pkgs.statix
    pkgs.deadnix
  ];
}
