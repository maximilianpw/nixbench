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
      get [ "rootCause" ] null arpCase == "l2-arp-failure"
      && sameFacts (get [ "facts" ] [] arpCase) arpFacts
    );
    "dns-diagnosis" = passes (
      get [ "rootCause" ] null dnsCase == "dns-resolution"
      && sameFacts (get [ "facts" ] [] dnsCase) dnsFacts
    );
    "unknown-cases" = passes (
      get [ "rootCause" ] null missingPrerequisitesCase == "unknown"
      && get [ "facts" ] null missingPrerequisitesCase == []
      && builtins.length (get [ "nextChecks" ] [] missingPrerequisitesCase) > 0
      && get [ "rootCause" ] null healthyDnsCase == "unknown"
      && get [ "facts" ] null healthyDnsCase == []
      && builtins.length (get [ "nextChecks" ] [] healthyDnsCase) > 0
    );
    "structured-human-output" = passes (
      builtins.isList (get [ "evidence" ] null arpCase)
      && builtins.length (get [ "evidence" ] [] arpCase) > 0
      && builtins.all (item: builtins.isString item && item != "") (get [ "evidence" ] [] arpCase)
      && builtins.isList (get [ "discarded" ] null arpCase)
      && builtins.all (item: builtins.isString item && item != "") (get [ "discarded" ] [] arpCase)
      && builtins.isList (get [ "evidence" ] null dnsCase)
      && builtins.length (get [ "evidence" ] [] dnsCase) > 0
      && builtins.all (item: builtins.isString item && item != "") (get [ "evidence" ] [] dnsCase)
      && builtins.isList (get [ "nextChecks" ] null dnsCase)
      && builtins.isList (get [ "evidence" ] null missingPrerequisitesCase)
      && builtins.isList (get [ "discarded" ] null missingPrerequisitesCase)
      && builtins.isList (get [ "nextChecks" ] null missingPrerequisitesCase)
    );
    "diagnostic-discipline" = passes (
      builtins.isList (get [ "discarded" ] null arpCase)
      && builtins.all (code: builtins.elem code (get [ "discarded" ] [] arpCase)) [
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
