{ homeManagerModule, ... }:
{
  imports = [
    homeManagerModule
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  homeConfiguration = {};

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;

    users.nixos = {
      programs.git.enable = true;
    };
  };
}
