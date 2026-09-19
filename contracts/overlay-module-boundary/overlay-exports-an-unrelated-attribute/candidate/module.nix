{ pkgs, ... }:
{
  systemd.user.services.petrified = {
    description = "petrified dynamic DNS updater";
    serviceConfig.ExecStart = "${pkgs.petrified}/bin/petrified";
    wantedBy = [ "default.target" ];
  };

  systemd.user.timers.petrified = {
    wantedBy = [ "timers.target" ];
    partOf = [ "petrified.service" ];
    timerConfig.OnCalendar = "hourly";
  };
}
