{
  description = "Benchmark harness for evaluating AI-written Nix code";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = {
    self,
    nixpkgs,
  }: let
    systems = ["x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin"];
    forAllSystems = f:
      builtins.listToAttrs (map (system: {
          name = system;
          value = f system;
        })
        systems);
  in {
    packages = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      default = pkgs.writeShellApplication {
        name = "nixbench";
        runtimeInputs = [pkgs.python3];
        text = ''
          exec ${pkgs.python3}/bin/python ${self}/bench.py "$@"
        '';
      };
    });

    apps = forAllSystems (system: {
      default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/nixbench";
      };
    });

    checks = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      unit =
        pkgs.runCommand "nixbench-unit-tests" {
          nativeBuildInputs = [
            pkgs.python3
            pkgs.nix
          ];
        } ''
          cd ${self}
          export NIX_CONFIG="experimental-features = nix-command flakes"
          export PYTHONDONTWRITEBYTECODE=1
          python -m unittest discover -s tests
          touch $out
        '';
    });

    devShells = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      default = pkgs.mkShell {
        packages = [
          pkgs.python3
          pkgs.nix
          pkgs.nodejs_24
          pkgs.nixfmt-rfc-style
          pkgs.statix
          pkgs.deadnix
          pkgs.nil
        ];
      };
    });

    formatter = forAllSystems (system: nixpkgs.legacyPackages.${system}.nixfmt-rfc-style);
  };
}
