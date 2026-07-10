# Keep Overlays And Module Options Separate

Edit `overlay.nix` and `module.nix`.

The starter tries to use an overlay both to package a tool and to define `systemd.user` configuration. Split those responsibilities correctly: the overlay should only customize packages, while the module should define the user service and timer.

Requirements:

- Keep `overlay.nix` in normal overlay form: `final: prev: { ... }`.
- Define only `petrified` in the overlay output.
- Build `petrified` with `prev.stdenv.mkDerivation`.
- Set `name = "petrified-2.0.3"`.
- Fetch the source with `prev.fetchurl` from `https://gitlab.com/troyengel/petrified/-/archive/v2.0.3/petrified-v2.0.3.tar.gz`.
- Keep `buildInputs = [ final.iproute final.curl ]`.
- Keep `installFlags = [ "DESTDIR=$(out)" ]`.
- Define the service and timer in `module.nix`, using `pkgs.petrified`.
- Set `systemd.user.services.petrified.description = "petrified dynamic DNS updater"`.
- Set `systemd.user.services.petrified.serviceConfig.ExecStart = "${pkgs.petrified}/bin/petrified"`.
- Set `systemd.user.services.petrified.wantedBy = [ "default.target" ]`.
- Set `systemd.user.timers.petrified.wantedBy = [ "timers.target" ]`.
- Set `systemd.user.timers.petrified.partOf = [ "petrified.service" ]`.
- Set `systemd.user.timers.petrified.timerConfig.OnCalendar = "hourly"`.
- Do not define `systemd.*` in the overlay.
- Do not define `petrified` in the module.

## Source Context

This task is modeled after a NixOS Discourse thread where a user tried to define a package and a user systemd timer through one overlay, then learned that overlays cannot set module options and that the package/module split has to be explicit.

- NixOS Discourse: https://discourse.nixos.org/t/overlay-with-user-systemd-unit-and-timer/9295
