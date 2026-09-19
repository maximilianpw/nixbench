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
      # hooks.command_not_found /nix/store/nix-index/bin/command-not-found
        ${pkgs.nix-index}/bin/command-not-found $command
      }

      # hooks.command_not_found
        ($hooks | default [] | append __nix_command_not_found)
      })
    '';
  };
}
