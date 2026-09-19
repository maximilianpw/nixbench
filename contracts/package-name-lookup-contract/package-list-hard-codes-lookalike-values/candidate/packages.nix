{ pkgs }:
{
  environment.systemPackages = [
    "git"
    "ripgrep"
    "fd"
    "bat"
    "eza"
    "nixfmt-rfc-style"
    "nil"
    "statix"
    "deadnix"
  ];
}
