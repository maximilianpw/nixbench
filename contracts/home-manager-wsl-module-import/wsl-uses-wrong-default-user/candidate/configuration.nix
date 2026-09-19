{ homeManagerModule, ... }:
{
  imports = [
    homeManagerModule
  ];

  wsl.enable = true;
  wsl.defaultUser = "alice";

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;

    users.nixos = {
      programs.git.enable = true;
    };
  };
}
