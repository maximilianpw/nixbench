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

## Test The Evaluator, Not Only The Reference

A passing reference and failing starter are necessary, but they do not show that an evaluator draws the right boundary. For each task, also keep adversarial contract cases that cover:

- A plausible-looking candidate that violates one important requirement and must fail.
- A semantically valid alternative that changes irrelevant details such as list order or prose and must pass.
- A second input when the candidate is a function, so hard-coded answers do not pass.
- Opaque sentinel values for fake packages and builders, rather than strings that are identical to their attribute names.

Repository-wide evaluator mutations live in `tests/test_evaluator_contracts.py`. Add a regression there whenever a real benchmark run exposes a false positive or false negative.

## Task Ideas

- Fix a NixOS module option type and conditional config.
- Convert a single-system flake into a per-system flake.
- Add `overrideAttrs` without dropping existing patches or metadata.
- Replace impure host paths with package inputs.
- Repair infinite recursion from self-referential attrsets.
- Compose module paths passed through arguments without confusing path addition, string interpolation, and list syntax.
- Package a Python, Rust, or Go app using fake builders first, then add real-build variants later.
