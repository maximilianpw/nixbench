# Overlay Package Override

Edit `overlay.nix`.

Write an overlay that:

- Overrides `prev.tinygrep` as `tinygrep`.
- Changes its version to `0.2.0`.
- Appends `./fix-musl.patch` to any existing patches.
- Sets `doCheck = true`.
- Preserves existing `meta` while setting `meta.broken = false`.
- Adds `tinygrep-debug` derived from `final.tinygrep` with `pname = "tinygrep-debug"` and `dontStrip = true`.

Use the normal overlay shape:

```nix
final: prev: { ... }
```
