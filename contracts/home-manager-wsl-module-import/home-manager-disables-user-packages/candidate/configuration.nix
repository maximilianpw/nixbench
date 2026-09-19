{ homeManagerModule, ... }:
{
  imports = [
    homeManagerModule
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = false;

    users.nixos = {
      programs.git.enable = true;
    };
  };
}
