{ pkgs, ... }:
{
  systemd.services.quote-runner.serviceConfig = {
    Type = "oneshot";
    StateDirectory = "quote-runner";
    ExecStart = "${pkgs.bash}/bin/bash -lc 'mkdir -p \"\${STATE_DIRECTORY}\" && printf \"%s\\n\" \"\${NIXBENCH_MESSAGE}\" >> \"\${STATE_DIRECTORY}/output.log\"'";
  };
}
