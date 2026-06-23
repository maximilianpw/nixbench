#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  diagnose = import ${workdir}/diagnosis.nix;
  arpCase = diagnose {
    observations = {
      physicalLink = "up";
      ipv4 = {
        hasAddress = true;
        hasDefaultRoute = true;
      };
      arp.gateway = "FAILED";
      dns.lookup = "fails";
      audio.hdmi = "suspicious";
    };
  };
  dnsCase = diagnose {
    observations = {
      physicalLink = "up";
      ipv4 = {
        hasAddress = true;
        hasDefaultRoute = true;
      };
      arp.gateway = "REACHABLE";
      dns.lookup = "fails";
    };
  };
in
assert arpCase.rootCause == "l2-arp-failure";
assert builtins.elem "gateway arp failed" arpCase.evidence;
assert builtins.elem "dns" arpCase.discarded;
assert builtins.elem "audio" arpCase.discarded;
assert builtins.elem "hdmi" arpCase.discarded;
assert !(builtins.elem "restart PipeWire" arpCase.nextChecks);
assert dnsCase.rootCause == "dns-resolution";
assert builtins.elem "gateway arp is reachable" dnsCase.evidence;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
