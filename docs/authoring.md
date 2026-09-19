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
release manifest. Every task starts or returns to `calibrating` after a digest
change. Generate draft evidence with `calibration-report`; do not hand-copy
aggregate claims or edit lifecycle state from the command. Activation requires
three materially different validated configurations with at least one valid
observation per task in each, plus manual accepted-alternative and evaluator-
dispute review and an explicit approval rationale. Optional repetitions improve
stability but do not replace those mandatory identities and reviews. Follow the
full workflow in [benchmark-governance.md](benchmark-governance.md).

Each case uses contract schema 3, names the rubric criterion it exercises,
and declares the complete expected criterion vector:

```toml
schema_version = 3
task_id = "package-stdenv-cli"
outcome = "reject"
criterion_id = "install-contract"
description = "The install command is present only in a comment."

[expected_criteria]
package-source = true
build-contract = true
install-contract = false
package-metadata = true
```

Every required criterion needs its own targeted rejecting case; a criterion
label on a passing fixture is not negative coverage. A passing case expects all
criteria true. A rejecting case expects its named criterion false and should
keep unrelated criteria true. If one plausible mutation necessarily causes
additional failures, list every such criterion and a reason in
`[coupled_failures]`. The loader rejects missing or unknown vector keys,
undocumented coupling, and a rejecting case whose named criterion is expected
true.

Candidate digests are part of the boundary inventory. Do not present the same
rejecting candidate as independent evidence for multiple criteria unless the
cases intentionally vary evaluator inputs and each manifest records a
`duplicate_candidate_reason`. Every task also keeps at least one passing
alternative whose materialized candidate differs from the reference.

Evaluators initialize every outcome to false and write the schema-2 score file
atomically. Make each criterion total: guard nested attribute access and keep
candidate-dependent evaluation inside that criterion's boundary so one missing
field does not erase unrelated credit. An ordinary whole-candidate syntax or
import failure may exit `1` with an all-false valid payload, but an isolated
missing field must not collapse the complete vector. Reserve exit codes `2`
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
