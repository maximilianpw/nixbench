#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
  get = path: default: value:
    if path == [] then value
    else if builtins.isAttrs value && builtins.hasAttr (builtins.head path) value
    then get (builtins.tail path) default (builtins.getAttr (builtins.head path) value)
    else default;
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
  rawModule = import ${workdir}/module.nix { pkgs = result; };
  module = if rawModule ? config then rawModule.config else rawModule;
  sourceHash = get [ "petrified" "src" "hash" ]
    (get [ "petrified" "src" "sha256" ] null result) result;
  service = get [ "systemd" "user" "services" "petrified" ] {} module;
  timer = get [ "systemd" "user" "timers" "petrified" ] {} module;
in {
  schema_version = 2;
  criteria = {
    "overlay-package" = passes (
      builtins.attrNames result == [ "petrified" ]
      && result.petrified.type == "derivation"
      && result.petrified.name == "petrified-2.0.3"
      && result.petrified.buildInputs == [ "/nix/store/final-iproute" "/nix/store/final-curl" ]
      && result.petrified.installFlags == [ "DESTDIR=\$(out)" ]
    );
    "pinned-source-build" = passes (
      result.petrified.src.__fetchurl == true
      && result.petrified.src.url == "https://gitlab.com/troyengel/petrified/-/archive/v2.0.3/petrified-v2.0.3.tar.gz"
      && sourceHash == "bb01029abc7796d2dd824f88beb2da05fb8da10ceb3ec7a0c1682631d670fc27"
    );
    "module-service" = passes (
      get [ "description" ] null service == "petrified dynamic DNS updater"
      && get [ "serviceConfig" "ExecStart" ] null service == "/nix/store/petrified-2.0.3/bin/petrified"
      && get [ "wantedBy" ] null service == [ "default.target" ]
    );
    "module-timer-boundary" = passes (
      !(builtins.hasAttr "petrified" module)
      && get [ "wantedBy" ] null timer == [ "timers.target" ]
      && get [ "partOf" ] null timer == [ "petrified.service" ]
      && get [ "timerConfig" "OnCalendar" ] null timer == "hourly"
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"overlay-package":false,"pinned-source-build":false,"module-service":false,"module-timer-boundary":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
