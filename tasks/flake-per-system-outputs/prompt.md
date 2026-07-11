# Per-System Flake Outputs

Edit `flake.nix`.

Create a self-contained flake with no external inputs. Its `outputs` function should define the systems:

```nix
[ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ]
```

For every system, expose:

- `packages.${system}.default` with `pname = "nixbench-sample"`, `version = "0.1.0"`, and the `system`.
- `packages`, `checks`, and `devShells` must contain derivations rather than plain attrsets so `nix flake check --no-build` accepts the flake. Keep the flake input-free by using `builtins.derivation` with Nix's `builtin:buildenv` builder for minimal derivations.
- `apps.${system}.default` with `type = "app"` and a `program` under the package output.
- `apps.${system}.default.meta.package = "nixbench-sample"`.
- `checks.${system}.eval` pointing at the package for that system.
- `devShells.${system}.default` with `name = "nixbench-dev"` and tools containing `nixfmt` and `statix`.

Also expose `lib.systems`.
