# Wrap FHS-Oriented Binaries

Edit `wrapper.nix`.

The starter tries to make NixOS more FHS-like by creating global directories. Replace that with explicit wrappers for software that expects an FHS environment.

Requirements:

- Return an attrset with `appimage` and `fhsEnv`.
- `appimage` must use `appimageTools.wrapType2`.
- Set `pname = "vendor-tool"` and `version = "2.0.0"` for the AppImage wrapper.
- Fetch the source with `fetchurl`.
- `fhsEnv` must use `buildFHSUserEnv`.
- Set `fhsEnv` name to `"vendor-tool-fhs"`.
- Include `alsa-lib`, `glib`, and `gtk3` from the provided package set in `targetPkgs`.
- Set `runScript = "vendor-tool"`.
- Do not create `/usr`, `/lib`, `/bin`, or `ld.so.conf` entries.

## Source Context

This task is modeled after threads where ChatGPT or generic Linux advice suggested manually creating FHS directories on NixOS. Community replies pointed toward explicit Nix mechanisms such as AppImage tooling, FHS user environments, patching, or `nix-ld`.

- Reddit: https://www.reddit.com/r/NixOS/comments/17tw9ik/filesystem_hierarchy/
- NixOS Discourse: https://discourse.nixos.org/t/newbie-question-about-running-appimage/41564
