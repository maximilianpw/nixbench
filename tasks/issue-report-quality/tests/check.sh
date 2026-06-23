#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  report = import ${workdir}/report.nix;
  text = builtins.toJSON report;
in
assert report.title != "";
assert report.failureClass == "evaluation";
assert report.system.system == "x86_64-linux";
assert report.system.nixosRelease == "25.05";
assert report.system.nixpkgsRevision == "8f3b2d1";
assert builtins.elem "nixos-rebuild test --flake .#workstation" report.reproduction;
assert builtins.elem "error: The option services.xserver.displayManager.sddm.enable does not exist" report.logs;
assert report.analysis.likelyFix == "Use services.displayManager.sddm.enable.";
assert report.confidence == "observed";
assert builtins.match ".*ChatGPT.*" text == null;
assert builtins.match ".*Copilot.*" text == null;
assert builtins.match ".*AI.*" text == null;
assert builtins.match ".*probably.*" text == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
