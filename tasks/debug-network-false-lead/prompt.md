# Debug Network Symptoms Without Chasing False Leads

Edit `diagnosis.nix`.

Implement a function with this shape:

```nix
{ observations }:
...
```

Return an attrset with:

- `rootCause`: one of `"l2-arp-failure"`, `"dns-resolution"`, or `"unknown"`.
- `evidence`: a list of short evidence strings.
- `discarded`: a list of false leads that should not be pursued.
- `nextChecks`: a list of concrete commands or checks.

Rules:

- If the physical link is up, an IPv4 address and default route exist, and gateway ARP is `FAILED`, diagnose `"l2-arp-failure"` even if DNS also fails.
- If gateway ARP is reachable but DNS lookup fails, diagnose `"dns-resolution"`.
- Do not blame audio, HDMI, PipeWire, or generic firewall issues when the observations point at ARP.

## Source Context

This task is modeled after NixOS Discourse help threads where ChatGPT was described as chasing diagnostic rabbit holes, including fixating on HDMI audio or other false leads instead of narrowing from observed evidence.

- NixOS Discourse: https://discourse.nixos.org/t/nixos-hard-locks-driving-my-crazy/72210
- NixOS Discourse: https://discourse.nixos.org/t/broken-state-of-the-system-after-25-11/73249
