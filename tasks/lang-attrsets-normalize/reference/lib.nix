{
  allSystems ? ["x86_64-linux" "aarch64-linux" "aarch64-darwin"],
  defaultSystem ? "x86_64-linux",
}: packages: let
  names = builtins.attrNames packages;

  supports = system: name: let
    package = packages.${name};
    enabled = !(package.disabled or false);
    listed = !(package ? systems) || builtins.elem system package.systems;
  in
    enabled && listed;

  namesFor = system: builtins.filter (supports system) names;
in {
  inherit defaultSystem names;
  versions = builtins.mapAttrs (_: package: package.version or "unknown") packages;
  bySystem = builtins.listToAttrs (map (system: {
      name = system;
      value = namesFor system;
    })
    allSystems);
  defaultPackages = namesFor defaultSystem;
}
