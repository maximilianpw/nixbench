{
  config,
  lib,
  pkgs,
}:

let
  cfg = config.programs.command-not-found;
  nushellEnabled = config.programs.nushell.enable or false;
in {
  config = lib.mkIf cfg.enable {
    environment.systemPackages = [
      pkgs.nix-index
    ];

    programs.bash.interactiveShellInit = ''
      source ${pkgs.nix-index}/etc/profile.d/command-not-found.sh
    '';

    programs.nushell.extraConfig = lib.mkIf nushellEnabled ''
      def __nix_command_not_found [command: string] {
        ${pkgs.nix-index}/bin/command-not-found $command
      }

      $env.config = ($env.config | upsert hooks.command_not_found {|hooks|
        ($hooks | default [] | append __nix_command_not_found)
      })
    '';
  };
}
