final: prev: {
  petrified = prev.stdenv.mkDerivation {
    name = "petrified-2.0.3";

    src = prev.fetchurl {
      url = "https://gitlab.com/troyengel/petrified/-/archive/v2.0.3/petrified-v2.0.3.tar.gz";
      sha256 = "bb01029abc7796d2dd824f88beb2da05fb8da10ceb3ec7a0c1682631d670fc27";
    };

    buildInputs = [ final.iproute final.curl ];
    installFlags = [ "DESTDIR=$(out)" ];
  };

  systemd.user.services.petrified = {
    description = "petrified dynamic DNS updater";
    serviceConfig.ExecStart = "${final.petrified}/bin/petrified";
    wantedBy = [ "default.target" ];
  };

  systemd.user.timers.petrified = {
    wantedBy = [ "timers.target" ];
    partOf = [ "petrified.service" ];
    timerConfig.OnCalendar = "hourly";
  };
}
