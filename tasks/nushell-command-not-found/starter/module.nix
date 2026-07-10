{
  config,
  lib,
  pkgs,
}:

let
  cfg = config.programs.command-not-found;
in {
  config = lib.mkIf cfg.enable {
    programs.bash.interactiveShellInit = ''
      source ${pkgs.nix-index}/etc/profile.d/command-not-found.sh
    '';
  };
}
