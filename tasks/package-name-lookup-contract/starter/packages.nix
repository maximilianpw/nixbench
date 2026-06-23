{ pkgs }:
{
  environment.systemPackages = [
    pkgs.git
    pkgs.ripgrep
    pkgs.fd
    pkgs.bat
    pkgs.exa
    pkgs.nixfmt
    pkgs."nix-language-server"
    pkgs.statix
    pkgs.deadnix
  ];
}
