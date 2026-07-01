# Keep Rust Builds Offline

Edit `package.nix`.

The package is a Rust application whose upstream build scripts normally try to download an ONNX Runtime binary and a model file during the build. Nix builds must stay pure and must not rely on network access from `build.rs`.

Rewrite the derivation so that:

- It still uses `rustPlatform.buildRustPackage`.
- It keeps `pname = "vision-indexer"` and `version = "0.4.0"`.
- It does not enable a Cargo feature named `download-binaries`.
- It uses a system ONNX Runtime dependency instead of asking Cargo to download one.
- It fetches the model file as a fixed Nix input with `fetchurl`.
- It exposes that fetched model as `passthru.assets.model`.
- It sets build-time environment variables telling the Rust build to use the system ONNX Runtime library and the pinned model path.
- It does not disable sandboxing or add options such as `__noChroot`.

Do not solve this by adding network access, shelling out to `curl`, or leaving URLs for build scripts to fetch at build time.

## Source Context

This task is modeled after recent reports where Rust packages tried to download prebuilt binaries or data during sandboxed Nix builds:

- NixOS Discourse: https://discourse.nixos.org/t/buildrustpackage-fails-to-download-prebuild-binary/78010
- NixOS Discourse: https://discourse.nixos.org/t/rust-package-appears-to-need-network-during-build/74334
