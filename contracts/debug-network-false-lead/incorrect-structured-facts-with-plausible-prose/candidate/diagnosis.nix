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
    facts = [ "gateway-arp-reachable" "dns-lookup-failed" ];
    evidence = [ "physical link is up; IPv4 address and route exist; gateway ARP failed" ];
    discarded = [ "dns" "audio" "hdmi" ];
    nextChecks = [ "inspect the neighbor table" ];
  } else if gatewayArp == "REACHABLE" && dnsFails then {
    rootCause = "dns-resolution";
    facts = [ "gateway-arp-failed" ];
    evidence = [ "gateway ARP is reachable and DNS lookup fails" ];
    discarded = [ "layer two failure" ];
    nextChecks = [ "inspect the resolver" ];
  } else {
    rootCause = "unknown";
    facts = [];
    evidence = [];
    discarded = [];
    nextChecks = [ "collect more observations" ];
  }
