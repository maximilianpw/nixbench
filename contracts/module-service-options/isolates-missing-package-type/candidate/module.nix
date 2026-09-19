{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.services.nixbench-agent;
in
{
  options.services.nixbench-agent = {
    enable = lib.mkEnableOption "the nixbench-agent service";
    package = lib.mkOption {
      default = pkgs.nixbench-agent;
    };
    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
    };
    extraArgs = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [];
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.nixbench-agent = {
      serviceConfig = {
        ExecStart =
          "${cfg.package}/bin/nixbench-agent --port ${toString cfg.port}"
          + " ${builtins.concatStringsSep " " cfg.extraArgs}";
      };
    };

    networking.firewall.allowedTCPPorts = [ cfg.port ];
  };
}
