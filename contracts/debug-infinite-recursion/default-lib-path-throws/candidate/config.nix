{
  lib ? {
    optional = condition: value: if condition then [value] else [];
    __default = true;
  },
}: let
  base = { name = "nixbench"; enableDocs = true; };
  result = base // { outputs = [base.name] ++ lib.optional base.enableDocs "manual"; };
in if lib ? __default then throw "default lib broken" else result
