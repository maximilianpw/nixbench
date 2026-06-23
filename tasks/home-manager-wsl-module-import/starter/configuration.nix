{ homeManagerModule, ... }:
let
  home-manager = {
    lib.homeManagerConfiguration = attrs: attrs;
  };
in
{
  imports = [
    <home-manager/nixos>
  ];

  wsl.enable = true;
  wsl.defaultUser = "nixos";

  homeConfiguration = home-manager.lib.homeManagerConfiguration {
    pkgs = null;
    modules = [
      {
        programs.git.enable = true;
      }
    ];
  };
}
