{
  lib ? {
    optionals = condition: values:
      if condition
      then values
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
    outputs = [base.name] ++ lib.optionals base.enableDocs ["manual"];
  }
