{ observations }:
let
  linkUp = observations.physicalLink or "" == "up";
  hasAddress = observations.ipv4.hasAddress or false;
  hasDefaultRoute = observations.ipv4.hasDefaultRoute or false;
  gatewayArp = observations.arp.gateway or "unknown";
  dnsFails = observations.dns.lookup or "ok" == "fails";
in
  if linkUp && hasAddress && hasDefaultRoute && gatewayArp == "FAILED" then {
    rootCause = "l2-arp-failure";
    facts = [ "physical-link-up" "ipv4-address-present" "default-route-present" "gateway-arp-failed" ];
    evidence = [ "The decisive observations are recorded in the fact codes." ];
    discarded = [ "audio" "hdmi" "pipewire" "generic-firewall" ];
    nextChecks = [ "Inspect the affected local segment." ];
  } else if gatewayArp == "REACHABLE" && dnsFails then {
    rootCause = "dns-resolution";
    facts = [ "gateway-arp-reachable" "dns-lookup-failed" ];
    evidence = [ "The recorded fact pair isolates this outcome." ];
    discarded = [ "Lower layers passed the relevant check." ];
    nextChecks = [ "Inspect the configured name service." ];
  } else {
    rootCause = "unknown";
    facts = [];
    evidence = [];
    discarded = [];
    nextChecks = [ "Collect more observations." ];
  }
