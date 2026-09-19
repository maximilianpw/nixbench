{ homeManagerModule, ... }:
{
  imports = [
    homeManagerModule
    { extra = true; }
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
