{ inputs, ... }:
{
  imports = [
    inputs.nixvim.homeManagerModules.nixvim
    inputs.agenix.homeManagerModules.default
  ];

  programs.git.enable = true;
}
