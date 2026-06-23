{
  lib ? {
    optional = condition: value:
      if condition
      then [value]
      else [];
  },
}: let
  config =
    config
    // {
      name = "nixbench";
      enableDocs = true;
      outputs = [config.name] ++ lib.optional config.enableDocs "manual";
    };
in
  config
