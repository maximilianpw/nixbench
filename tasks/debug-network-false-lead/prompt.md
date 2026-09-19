# Debug Network Symptoms Without Chasing False Leads

Edit `diagnosis.nix`.

Implement a function with this shape:

```nix
{ observations }:
...
```

`observations` has this schema:

```nix
{
  physicalLink = "up" | "down" | "unknown";
  ipv4.hasAddress = true | false;
  ipv4.hasDefaultRoute = true | false;
  arp.gateway = "FAILED" | "REACHABLE" | "unknown";
  dns.lookup = "fails" | "ok" | "unknown";
  audio = { ... }; # optional and never diagnostic for the required outcomes
}
```

Return an attrset with:

- `rootCause`: one of `"l2-arp-failure"`, `"dns-resolution"`, or `"unknown"`.
- `facts`: a list containing only the fact codes below that support the diagnosis.
- `evidence`: a list of short evidence strings.
- `discarded`: a list of structured false-lead codes that should not be pursued.
- `nextChecks`: a list of concrete commands or checks.

Rules:

- If the physical link is up, an IPv4 address and default route exist, and gateway ARP is `FAILED`, diagnose `"l2-arp-failure"` even if DNS also fails.
- If gateway ARP is reachable but DNS lookup fails, diagnose `"dns-resolution"`.
- For `"l2-arp-failure"`, return `"physical-link-up"`, `"ipv4-address-present"`, `"default-route-present"`, and `"gateway-arp-failed"` in `facts`.
- For `"dns-resolution"`, return `"gateway-arp-reachable"` and `"dns-lookup-failed"` in `facts`.
- For `"unknown"`, return an empty `facts` list.
- Do not blame audio, HDMI, PipeWire, or generic firewall issues when the observations point at ARP.
- For `"l2-arp-failure"`, include `"audio"`, `"hdmi"`, `"pipewire"`, and
  `"generic-firewall"` in `discarded`. These codes are the machine-graded
  diagnostic-discipline record; explanatory prose remains free-form.
- Evidence wording is free-form for human readers. The evaluator grades `rootCause` and `facts`, not words in `evidence`.

## Source Context

This task is modeled after NixOS Discourse help threads where ChatGPT was described as chasing diagnostic rabbit holes, including fixating on HDMI audio or other false leads instead of narrowing from observed evidence.

- NixOS Discourse: https://discourse.nixos.org/t/nixos-hard-locks-driving-my-crazy/72210
- NixOS Discourse: https://discourse.nixos.org/t/broken-state-of-the-system-after-25-11/73249
