# NixOS Service Module Options

Edit `module.nix`.

Write a NixOS-style module for `services.nixbench-agent`.

Requirements:

- Define `enable` with `lib.mkEnableOption`.
- Define `package` with default `pkgs.nixbench-agent`.
- Define `port` with type `lib.types.port`, default `8080`.
- Define `extraArgs` as a list of strings, default `[]`.
- When enabled, create `systemd.services.nixbench-agent`.
- `ExecStart` must run `${cfg.package}/bin/nixbench-agent --port ${toString cfg.port}` plus any `extraArgs`.
- Add the selected port to `networking.firewall.allowedTCPPorts`.
- Use `lib.mkIf cfg.enable` for conditional config.
