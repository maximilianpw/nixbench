{ pkgs, ... }:
let
  message = builtins.getEnv "NIXBENCH_MESSAGE";
in
{
  systemd.services.quote-runner.serviceConfig = {
    Type = "oneshot";
    StateDirectory = "quote-runner";
    ExecStart = "${pkgs.bash}/bin/bash -lc 'printf \"%s\\n\" \"${message}\" >> \"${STATE_DIRECTORY}/output.log\"'";
  };
}
