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
  missingPrerequisitesCase = diagnose {
    observations = {
      physicalLink = "down";
      ipv4 = {
        hasAddress = false;
        hasDefaultRoute = false;
      };
      arp.gateway = "FAILED";
      dns.lookup = "fails";
    };
  };
  healthyDnsCase = diagnose {
    observations = {
      physicalLink = "up";
      ipv4 = {
        hasAddress = true;
        hasDefaultRoute = true;
      };
      arp.gateway = "REACHABLE";
      dns.lookup = "ok";
    };
  };
  arpEvidence = builtins.concatStringsSep " " arpCase.evidence;
  dnsEvidence = builtins.concatStringsSep " " dnsCase.evidence;
  arpDiscarded = builtins.concatStringsSep " " arpCase.discarded;
  arpNextChecks = builtins.concatStringsSep " " arpCase.nextChecks;
in
assert arpCase.rootCause == "l2-arp-failure";
assert builtins.isList arpCase.evidence;
assert builtins.length arpCase.evidence > 0;
assert builtins.match ".*([Aa][Rr][Pp]|[Gg]ateway).*" arpEvidence != null;
assert builtins.match ".*([Ff]ail|[Uu]nreachable|[Ii]ncomplete).*" arpEvidence != null;
assert builtins.match ".*([Aa]udio|[Hh][Dd][Mm][Ii]|[Pp]ipe[Ww]ire|[Ff]irewall).*" arpEvidence == null;
assert builtins.match ".*[Dd][Nn][Ss].*" arpDiscarded != null;
assert builtins.match ".*[Aa]udio.*" arpDiscarded != null;
assert builtins.match ".*[Hh][Dd][Mm][Ii].*" arpDiscarded != null;
assert builtins.match ".*([Aa]udio|[Hh][Dd][Mm][Ii]|[Pp]ipe[Ww]ire|[Ff]irewall).*" arpNextChecks == null;
assert dnsCase.rootCause == "dns-resolution";
assert builtins.isList dnsCase.evidence;
assert builtins.length dnsCase.evidence > 0;
assert builtins.match ".*([Dd][Nn][Ss]|[Nn]ame resolution).*" dnsEvidence != null;
assert builtins.match ".*([Rr]eachable|[Gg]ateway|[Aa][Rr][Pp]).*" dnsEvidence != null;
assert builtins.match ".*([Aa]udio|[Hh][Dd][Mm][Ii]|[Pp]ipe[Ww]ire|[Ff]irewall).*" dnsEvidence == null;
assert builtins.isList dnsCase.nextChecks;
assert builtins.length dnsCase.nextChecks > 0;
assert missingPrerequisitesCase.rootCause == "unknown";
assert builtins.isList missingPrerequisitesCase.evidence;
assert builtins.isList missingPrerequisitesCase.discarded;
assert builtins.isList missingPrerequisitesCase.nextChecks;
assert builtins.length missingPrerequisitesCase.nextChecks > 0;
assert healthyDnsCase.rootCause == "unknown";
assert builtins.isList healthyDnsCase.nextChecks;
assert builtins.length healthyDnsCase.nextChecks > 0;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
