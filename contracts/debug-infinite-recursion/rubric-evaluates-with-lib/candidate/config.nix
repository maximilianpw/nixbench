{ lib ? { optional = c: v: if c then [ v ] else []; } }:
let name = "nixbench"; enableDocs = true; in { inherit name enableDocs; outputs = [ name ] ++ lib.optional enableDocs "manual"; }
