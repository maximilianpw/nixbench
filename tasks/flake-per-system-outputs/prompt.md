# Per-System Flake Outputs

Edit `flake.nix`.

Create a self-contained flake with no external inputs. Its `outputs` function should define the systems:

```nix
[ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ]
```

For every system, expose:

- `packages.${system}.default` with `pname = "nixbench-sample"`, `version = "0.1.0"`, and the `system`.
- `apps.${system}.default` with `type = "app"`.
- `checks.${system}.eval` pointing at the package for that system.
- `devShells.${system}.default` with `name = "nixbench-dev"` and tools containing `nixfmt` and `statix`.

Also expose `lib.systems`.
