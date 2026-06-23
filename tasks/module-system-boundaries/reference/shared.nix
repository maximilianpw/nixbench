{ pkgs }:
let
  shared = {
    packages = [
      pkgs.ripgrep
      pkgs.fd
    ];
    shell = "fish";
  };
in
{
  inherit shared;

  nixosModule = { ... }: {
    programs.fish.enable = true;
    environment.systemPackages = shared.packages;
  };

  homeManagerModule = { ... }: {
    programs.fish.enable = true;
    home.packages = shared.packages;
  };

  darwinModule = { ... }: {
    programs.fish.enable = true;
    environment.systemPackages = shared.packages;
  };
}
