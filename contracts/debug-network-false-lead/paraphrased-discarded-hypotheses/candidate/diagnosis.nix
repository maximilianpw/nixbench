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
    evidence = [
      "The local link has carrier and an IPv4 address and route are configured."
      "The next-hop neighbor cannot be resolved."
    ];
    discarded = [ "audio" "hdmi" "pipewire" "generic-firewall" ];
    nextChecks = [ "Inspect the neighbor table and layer-two path." ];
  } else if gatewayArp == "REACHABLE" && dnsFails then {
    rootCause = "dns-resolution";
    facts = [ "gateway-arp-reachable" "dns-lookup-failed" ];
    evidence = [
      "The next-hop neighbor responds."
      "Name resolution returns an error."
    ];
    discarded = [ "Lower-layer connectivity is working." ];
    nextChecks = [ "Query the configured resolver directly." ];
  } else {
    rootCause = "unknown";
    facts = [];
    evidence = [];
    discarded = [];
    nextChecks = [ "Collect address, route, and journal data." ];
  }
