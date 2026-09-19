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
    evidence = [ "The network is not working." ];
    discarded = [ "dns" "audio" "hdmi" ];
    nextChecks = [ "Collect route details." ];
  } else if gatewayArp == "REACHABLE" && dnsFails then {
    rootCause = "dns-resolution";
    evidence = [ "The network is not working." ];
    discarded = [ "l2-arp-failure" "audio" "hdmi" ];
    nextChecks = [ "Inspect the resolver." ];
  } else {
    rootCause = "unknown";
    evidence = [];
    discarded = [];
    nextChecks = [ "Collect more details." ];
  }
