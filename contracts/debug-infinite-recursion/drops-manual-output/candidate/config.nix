{ lib ? { optional = c: v: if c then [ v ] else []; } }: { name = "nixbench"; enableDocs = true; outputs = [ "nixbench" ]; }
