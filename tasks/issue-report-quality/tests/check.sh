#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  report = import ${workdir}/report.nix;
  text = builtins.toJSON report;
  analysisText = builtins.toJSON report.analysis;
in
assert builtins.isString report.title;
assert report.title != "";
assert report.failureClass == "evaluation";
assert report.system.system == "x86_64-linux";
assert report.system.nixosRelease == "25.05";
assert report.system.nixpkgsRevision == "8f3b2d1";
assert builtins.elem "nixos-rebuild test --flake .#workstation" report.reproduction;
assert builtins.isString report.expected;
assert report.expected != "";
assert builtins.match ".*([Ee]valuat|[Ss]ucceed).*" report.expected != null;
assert builtins.match ".*([Cc]urrent|SDDM|services[.]displayManager[.]sddm[.]enable).*" report.expected != null;
assert builtins.isString report.actual;
assert report.actual != "";
assert builtins.match ".*services[.]xserver[.]displayManager[.]sddm[.]enable.*" report.actual != null;
assert builtins.match ".*([Ee]valuat|[Ee]rror|[Ff]ail|does not exist).*" report.actual != null;
assert builtins.elem "error: The option services.xserver.displayManager.sddm.enable does not exist" report.logs;
assert builtins.isAttrs report.analysis;
assert builtins.isList report.analysis.observed;
assert builtins.isString report.analysis.likelyFix;
assert builtins.isList report.analysis.unverified;
assert builtins.match ".*services[.]xserver[.]displayManager[.]sddm[.]enable.*" analysisText != null;
assert builtins.match ".*services[.]displayManager[.]sddm[.]enable.*" analysisText != null;
assert !(report.analysis ? rootCause);
assert !(report.analysis ? confirmedRootCause);
assert report.confidence == "observed";
assert builtins.match ".*[Cc][Hh][Aa][Tt][Gg][Pp][Tt].*" text == null;
assert builtins.match ".*[Cc][Oo][Pp][Ii][Ll][Oo][Tt].*" text == null;
assert builtins.match ".*[^A-Za-z][Aa][Ii][^A-Za-z].*" text == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
