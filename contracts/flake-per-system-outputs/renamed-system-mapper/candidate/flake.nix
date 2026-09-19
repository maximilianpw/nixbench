{
  description = "Self-contained per-system flake exercise";

  outputs = {self}: let
    systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin"];
    mapSystems = f:
      builtins.listToAttrs (map (system: {
          name = system;
          value = f system;
        })
        systems);

    emptyManifest = builtins.toFile "nixbench-empty-buildenv-manifest.json" "[]";
    mkEmptyDerivation = {
      name,
      system,
      extra ? {},
    }:
      builtins.derivation (
        {
          inherit name system;
          builder = "builtin:buildenv";
          manifest = emptyManifest;
          derivations = [];
        }
        // extra
      );

    packages = mapSystems (system: {
      default = mkEmptyDerivation {
        name = "nixbench-sample-0.1.0";
        inherit system;
        extra = {
          pname = "nixbench-sample";
          version = "0.1.0";
        };
      };
    });
  in {
    lib.systems = systems;
    inherit packages;

    apps = mapSystems (system: {
      default = {
        type = "app";
        program = "${packages.${system}.default}/bin/nixbench-sample";
        meta.package = packages.${system}.default.pname;
      };
    });

    checks = mapSystems (system: {
      eval = packages.${system}.default;
    });

    devShells = mapSystems (system: {
      default = mkEmptyDerivation {
        name = "nixbench-dev";
        inherit system;
        extra.tools = ["nixfmt" "statix"];
      };
    });
  };
}
