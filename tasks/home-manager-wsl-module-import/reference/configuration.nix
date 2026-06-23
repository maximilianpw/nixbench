{ homeManagerModule, ... }:
{
  imports = [
    homeManagerModule
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;

    users.nixos = {
      programs.git.enable = true;
    };
  };
}
