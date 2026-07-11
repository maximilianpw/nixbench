#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makeDrv = attrs:
    attrs
    // {
      type = "derivation";
      outPath = "/nix/store/\${attrs.name}";
      __toString = self: self.outPath;
    };
  overlay = import ${workdir}/overlay.nix;
  base = {
    stdenv.mkDerivation = attrs: makeDrv attrs;
    fetchurl = attrs: attrs // { __fetchurl = true; };
    iproute = "/nix/store/iproute";
    curl = "/nix/store/curl";
  };
  final = base // result // {
    stdenv.mkDerivation = _: throw "overlay must build with prev.stdenv";
    fetchurl = _: throw "overlay must fetch with prev.fetchurl";
    iproute = "/nix/store/final-iproute";
    curl = "/nix/store/final-curl";
  };
  result = overlay final base;
  module = import ${workdir}/module.nix { pkgs = result; };
  service = module.systemd.user.services.petrified;
  timer = module.systemd.user.timers.petrified;
in
assert builtins.attrNames result == [ "petrified" ];
assert result.petrified.type == "derivation";
assert result.petrified.name == "petrified-2.0.3";
assert result.petrified.src.__fetchurl == true;
assert result.petrified.src.url == "https://gitlab.com/troyengel/petrified/-/archive/v2.0.3/petrified-v2.0.3.tar.gz";
assert result.petrified.src.sha256 == "bb01029abc7796d2dd824f88beb2da05fb8da10ceb3ec7a0c1682631d670fc27";
assert result.petrified.buildInputs == [ "/nix/store/final-iproute" "/nix/store/final-curl" ];
assert result.petrified.installFlags == [ "DESTDIR=\$(out)" ];
assert !(builtins.hasAttr "petrified" module);
assert service.description == "petrified dynamic DNS updater";
assert service.serviceConfig.ExecStart == "/nix/store/petrified-2.0.3/bin/petrified";
assert service.wantedBy == [ "default.target" ];
assert timer.wantedBy == [ "timers.target" ];
assert timer.partOf == [ "petrified.service" ];
assert timer.timerConfig.OnCalendar == "hourly";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
