#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  module = import ${workdir}/module.nix {};
  cfg = module.config;
in
assert cfg.services.displayManager.sddm.enable == true;
assert cfg.services.desktopManager.plasma6.enable == true;
assert cfg.hardware.graphics.enable == true;
assert cfg.programs.kdeconnect.enable == true;
assert !(cfg.services ? xserver);
assert !(cfg.hardware ? opengl);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
