{
  lib ? {
    optional = condition: value:
      if condition
      then [value]
      else [];
  },
}: let
  base = {
    name = "nixbench";
    enableDocs = true;
  };
in
  base
  // {
    outputs = [base.name] ++ lib.optional base.enableDocs "manual";
  }
