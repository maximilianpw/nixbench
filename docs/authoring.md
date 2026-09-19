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

Store evaluator cases under `contracts/<task-id>/<case-id>/`. Add a regression whenever a real benchmark run exposes a false positive or false negative.

Before activation, the corpus release check also requires deterministic
repeated outcomes, no invalid measurements or known-issue skips, evaluator
runtime below 80 percent of the task timeout, a release note, and a checked
release manifest. Follow the calibration and lifecycle rules in
[benchmark-governance.md](benchmark-governance.md).

Each case uses contract schema 2 and names the rubric criterion it exercises:

```toml
schema_version = 2
task_id = "package-stdenv-cli"
outcome = "reject"
criterion_id = "install-contract"
description = "The install command is present only in a comment."
```

Keep at least one case for every required criterion. A rejecting case leaves
its named criterion false. A passing case leaves it true.

Evaluators initialize every outcome to false and write the schema-2 score file
atomically. Evaluate criteria independently where possible so one missing
attribute does not erase credit for unrelated requirements. Candidate syntax
or evaluation failures exit `1` with a valid payload. Reserve exit codes `2`
and greater for evaluator implementation or infrastructure failures.

Hidden cases may vary inputs and expose edge conditions. Hidden evaluators may not require an undocumented representation when common semantic alternatives exist.

## Task Ideas

- Fix a NixOS module option type and conditional config.
- Convert a single-system flake into a per-system flake.
- Add `overrideAttrs` without dropping existing patches or metadata.
- Replace impure host paths with package inputs.
- Repair infinite recursion from self-referential attrsets.
- Compose module paths passed through arguments without confusing path addition, string interpolation, and list syntax.
- Package a Python, Rust, or Go app using fake builders first, then add real-build variants later.
