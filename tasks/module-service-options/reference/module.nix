{
  config,
  lib,
  pkgs,
  ...
}: let
  cfg = config.services.nixbench-agent;
in {
  options.services.nixbench-agent = {
    enable = lib.mkEnableOption "nixbench agent";

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.nixbench-agent;
      description = "Package providing the nixbench-agent executable.";
    };

    port = lib.mkOption {
      type = lib.types.port;
      default = 8080;
      description = "TCP port for the nixbench agent.";
    };

    extraArgs = lib.mkOption {
      type = lib.types.listOf lib.types.str;
      default = [];
      description = "Additional command line arguments for nixbench-agent.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.services.nixbench-agent = {
      wantedBy = ["multi-user.target"];
      after = ["network-online.target"];
      wants = ["network-online.target"];
      serviceConfig = {
        ExecStart = "${cfg.package}/bin/nixbench-agent --port ${toString cfg.port} ${builtins.concatStringsSep " " cfg.extraArgs}";
        DynamicUser = true;
        Restart = "on-failure";
      };
    };

    networking.firewall.allowedTCPPorts = [cfg.port];
  };
}
