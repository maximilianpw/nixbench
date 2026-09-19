{ pkgs }:
let
  shared = {
    packages = [ pkgs.ripgrep pkgs.fd ];
    shell = "fish";
  };
  mkModule = packageConfig: { ... }:
    packageConfig // { programs.fish.enable = true; };
in {
  inherit shared;
  nixosModule = mkModule { environment.systemPackages = shared.packages; };
  homeManagerModule = mkModule { home.packages = shared.packages; };
  darwinModule = mkModule { environment.systemPackages = shared.packages; };
}
