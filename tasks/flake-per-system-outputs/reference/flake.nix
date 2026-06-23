{
  description = "Self-contained per-system flake exercise";

  outputs = {self}: let
    systems = ["x86_64-linux" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = f:
      builtins.listToAttrs (map (system: {
          name = system;
          value = f system;
        })
        systems);

    packages = forAllSystems (system: {
      default = {
        pname = "nixbench-sample";
        version = "0.1.0";
        inherit system;
      };
    });
  in {
    lib.systems = systems;
    inherit packages;

    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "/nix/store/placeholder-nixbench-sample/bin/nixbench-sample";
        meta.package = packages.${system}.default.pname;
      };
    });

    checks = forAllSystems (system: {
      eval = packages.${system}.default;
    });

    devShells = forAllSystems (system: {
      default = {
        name = "nixbench-dev";
        tools = ["nixfmt" "statix"];
        inherit system;
      };
    });
  };
}
