{ observations }:
{
  rootCause = "dns-resolution";
  evidence = [
    "DNS lookup failed"
  ];
  discarded = [];
  nextChecks = [
    "change DNS servers"
    "restart PipeWire"
  ];
}
