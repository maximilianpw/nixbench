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
  sameFacts = actual: expected:
    builtins.length actual == builtins.length expected
    && builtins.all (fact: builtins.elem fact actual) expected
    && builtins.all (fact: builtins.elem fact expected) actual;
  arpFacts = [
    "physical-link-up"
    "ipv4-address-present"
    "default-route-present"
    "gateway-arp-failed"
  ];
  dnsFacts = [ "gateway-arp-reachable" "dns-lookup-failed" ];
in {
  schema_version = 2;
  criteria = {
    "arp-diagnosis" = passes (
      arpCase.rootCause == "l2-arp-failure" && sameFacts arpCase.facts arpFacts
    );
    "dns-diagnosis" = passes (
      dnsCase.rootCause == "dns-resolution" && sameFacts dnsCase.facts dnsFacts
    );
    "unknown-cases" = passes (
      missingPrerequisitesCase.rootCause == "unknown"
      && missingPrerequisitesCase.facts == []
      && builtins.length missingPrerequisitesCase.nextChecks > 0
      && healthyDnsCase.rootCause == "unknown"
      && healthyDnsCase.facts == []
      && builtins.length healthyDnsCase.nextChecks > 0
    );
    "structured-human-output" = passes (
      builtins.isList arpCase.evidence
      && builtins.length arpCase.evidence > 0
      && builtins.all (item: builtins.isString item && item != "") arpCase.evidence
      && builtins.isList arpCase.discarded
      && builtins.all (item: builtins.isString item && item != "") arpCase.discarded
      && builtins.isList dnsCase.evidence
      && builtins.length dnsCase.evidence > 0
      && builtins.all (item: builtins.isString item && item != "") dnsCase.evidence
      && builtins.isList dnsCase.nextChecks
      && builtins.isList missingPrerequisitesCase.evidence
      && builtins.isList missingPrerequisitesCase.discarded
      && builtins.isList missingPrerequisitesCase.nextChecks
    );
    "diagnostic-discipline" = passes (
      builtins.isList arpCase.discarded
      && builtins.all (code: builtins.elem code arpCase.discarded) [
        "audio" "hdmi" "pipewire" "generic-firewall"
      ]
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"arp-diagnosis":false,"dns-diagnosis":false,"unknown-cases":false,"structured-human-output":false,"diagnostic-discipline":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
