# Escape Shell Variables In Nix Strings

Edit `service.nix`.

Define a systemd service named `quote-runner` whose `ExecStart` runs Bash and appends the runtime environment variable `NIXBENCH_MESSAGE` to `${STATE_DIRECTORY}/output.log`.

Requirements:

- Use `${pkgs.bash}/bin/bash`.
- Set `serviceConfig.Type = "oneshot"`.
- Set `serviceConfig.StateDirectory = "quote-runner"`.
- `ExecStart` must contain the literal shell variables `${NIXBENCH_MESSAGE}` and `${STATE_DIRECTORY}` for systemd/Bash to expand at runtime.
- Do not use `builtins.getEnv`, `/usr/bin`, `/bin/sh`, or a host path.

## Source Context

This task is modeled after a NixOS Discourse thread where a user noted that even frontier models repeatedly make Nix character escaping mistakes, especially around injected code.

- NixOS Discourse: https://discourse.nixos.org/t/local-ai-agent-for-nixos-configuration-looking-for-experience-reports/77238
