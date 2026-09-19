{ pkgs }:
let
  shared = { packages = [ pkgs.fd pkgs.ripgrep ]; shell = "fish"; };
in {
  inherit shared;
  nixosModule = { ... }: { programs.fish.enable = true; environment.systemPackages = [ pkgs.ripgrep pkgs.fd ]; };
  homeManagerModule = { ... }: { programs.fish.enable = true; home.packages = [ pkgs.fd pkgs.ripgrep ]; };
  darwinModule = { ... }: { programs.fish.enable = true; environment.systemPackages = [ pkgs.ripgrep pkgs.fd ]; };
}
