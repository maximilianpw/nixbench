# Normalize Package Attribute Sets

Edit `lib.nix`.

Implement a function with this shape:

```nix
{ allSystems ? [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ]
, defaultSystem ? "x86_64-linux"
}:
packages:
...
```

The result must include:

- `defaultSystem`: the selected default system.
- `names`: sorted package names from the input attrset, including disabled packages.
- `versions`: an attrset mapping each package name to `version`, or `"unknown"` when missing, including disabled packages.
- `bySystem`: an attrset mapping every system in `allSystems` to the package names supported on that system.
- `defaultPackages`: package names supported on `defaultSystem`.

A package supports all systems when it has no `systems` field. Disabled packages still appear in `names` and `versions`; exclude them only from `bySystem` and `defaultPackages`.
