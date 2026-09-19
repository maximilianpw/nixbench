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
      "physical link is up"
      "ipv4 address and default route are present"
      "audio and HDMI are the cause"
    ];
    discarded = [ "dns" ];
    nextChecks = [
      "ip neigh show dev <interface>"
      "arping <gateway>"
      "inspect bridge or vlan configuration"
    ];
  } else if gatewayArp == "REACHABLE" && dnsFails then {
    rootCause = "dns-resolution";
    facts = [ "gateway-arp-reachable" "dns-lookup-failed" ];
    evidence = [
      "audio appears healthy"
      "dns lookup fails"
    ];
    discarded = [
      "l2-arp-failure"
      "audio"
      "hdmi"
    ];
    nextChecks = [
      "resolvectl status"
      "dig @<resolver> example.com"
    ];
  } else {
    rootCause = "unknown";
    facts = [];
    evidence = [];
    discarded = [
      "audio"
      "hdmi"
    ];
    nextChecks = [
      "collect ip addr, ip route, and journal logs"
    ];
  }
