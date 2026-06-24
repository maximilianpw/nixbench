# Authoring Tasks

Good NixBench tasks should test Nix skill directly, not incidental knowledge of a particular package.

## Prefer

- Self-contained evaluators.
- Fake `stdenv`, `lib`, and package sets for structure tests.
- Small hidden inputs that catch hardcoding.
- Clear file targets in the prompt.
- Reference solutions that are boring and idiomatic.

## Avoid

- Network fetches in evaluators.
- Large real builds unless the task explicitly measures packaging integration.
- Prompts that leak the exact hidden assertions.
- Checks that only look for strings when Nix evaluation can inspect the value.

## Task Ideas

- Fix a NixOS module option type and conditional config.
- Convert a single-system flake into a per-system flake.
- Add `overrideAttrs` without dropping existing patches or metadata.
- Replace impure host paths with package inputs.
- Repair infinite recursion from self-referential attrsets.
- Compose module paths passed through arguments without confusing path addition, string interpolation, and list syntax.
- Package a Python, Rust, or Go app using fake builders first, then add real-build variants later.
