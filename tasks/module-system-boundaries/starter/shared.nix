{ pkgs }:
let
  shared = {
    packages = [
      pkgs.ripgrep
      pkgs.fd
    ];
    shell = "fish";
  };

  mixedModule = { ... }: {
    programs.fish.enable = true;
    environment.systemPackages = shared.packages;
    home.packages = shared.packages;
  };
in
{
  inherit shared;
  nixosModule = mixedModule;
  homeManagerModule = mixedModule;
  darwinModule = mixedModule;
}
