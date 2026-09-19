# Plan 010: Gate current website exports through checked releases and publication validation

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update this plan's row in
> `plans/README.md` unless a reviewer told you they maintain the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- nixbench/export.py nixbench/cli.py nixbench/release.py tests/test_export.py tests/test_cli.py docs/running-agents.md docs/reproducibility.md scripts/run-current-studies.sh`
> This plan assumes Plan 009's shared current-study validator exists. Stop if it
> does not.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: `plans/009-strict-study-publication-validation.md`
- **Category**: bug
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

`export-site` is the path that feeds public benchmark data to the website, but
it currently performs a separate, weaker set of checks and never invokes the
formal release publication gate. This allows current rows from an unreleased
corpus, a mismatched task matrix, or self-asserted protocol identity to reach
the site even when `publication-check` would reject them. Current-protocol site
exports should be a presentation transform over already validated publication
evidence.

## Current state

- `nixbench/export.py:29-40` accepts result/output settings but no release
  manifest.
- `nixbench/export.py:84-112` groups studies by self-declared corpus digest and
  configuration ID.
- `nixbench/export.py:135-170` checks presence and formatting of identity fields
  but does not load a checked release manifest or call `check_publication`.
- `docs/running-agents.md:89-106` describes `export-site` as a publication gate
  that rejects mixed identities and invalid observations.
- Private-heldout and retired studies are already refused for direct public-site
  export. Preserve that policy; this plan is not a private redaction redesign.
- Existing historical rows use `--allow-legacy-protocol`. Keep legacy import
  explicit and visibly separate from current release-backed export.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Export tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_export tests.test_cli -v` | all pass |
| Full suite | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests` | exit 0 with system dependencies |
| CLI help | `python3 bench.py export-site --help` | documents required release manifest for current studies |
| Site tests | `cd site && pnpm test` | all pass |
| Site build | `cd site && pnpm build` | exit 0 |

## Scope

**In scope**:
- `nixbench/export.py`
- `nixbench/cli.py`
- `nixbench/release.py` only for reusable manifest-loading/publication helpers
- `tests/test_export.py`
- `tests/test_cli.py`
- `docs/running-agents.md`
- `docs/reproducibility.md`
- `scripts/run-current-studies.sh` if it invokes export and needs the manifest argument

**Out of scope**:
- Site component/UI changes.
- Private-heldout redacted publication format.
- Rewriting existing `site/src/data/benchmark-trials.json` without explicit
  operator direction.
- Weakening the current minimum-trials or expected-configuration checks.
- Automatically publishing artifacts.

## Git workflow

- Suggested branch: `advisor/010-gate-site-export-through-release`
- Suggested commit: `fix: require release validation for site export`
- Do not deploy the site or publish generated data.

## Steps

### Step 1: Add a checked release-manifest input to current export

Add a CLI argument such as:

```text
--release-manifest corpus/releases/<version>.json
```

For any current protocol-complete study, this argument is mandatory. Load and
validate the manifest using production release code rather than ad hoc JSON
field access in `export.py`.

Legacy-only export may retain `--allow-legacy-protocol` without a current
release manifest, but mixed current and legacy inputs must have explicit,
well-tested behavior. Prefer requiring the manifest whenever any current study
is selected.

**Verify**: CLI tests show a current export without the manifest fails before
writing the output file.

### Step 2: Run strict publication validation for each current study

Before grouping or reporting a current study:

1. validate it through Plan 009's shared validator;
2. call `check_publication(study, release_manifest=manifest)`;
3. reject the export with the study path and all publication reasons if
   ineligible.

Do not continue past rejected studies and do not partially rewrite the output.
Preserve the existing atomic/no-modification-on-failure behavior tested by the
export suite.

**Verify**: add negative tests for wrong corpus digest, wrong task set, invalid
normalized score, unreleased corpus version, and missing completion evidence.
The output file must remain byte-for-byte unchanged.

### Step 3: Build groups only from validated identities

After publication validation, group studies by validated corpus and
configuration identities. Do not group first and validate later. Ensure a
configuration cannot combine studies from different release manifests,
protocol schema versions, adapter bundles, or task matrices.

Retain minimum-trial and expected-configuration checks as additional site
publication policy, not substitutes for release validation.

**Verify**: a test with two studies sharing a self-asserted configuration ID but
having different controlled protocol data must reject rather than merge.

### Step 4: Keep legacy import visibly separate

Legacy aggregate-only rows may still be imported only with
`--allow-legacy-protocol`. They must:

- never be merged into current release-backed configuration aggregates;
- retain legacy scoring/protocol labels;
- not satisfy expected-current-configuration counts;
- not bypass private/retired visibility restrictions.

**Verify**: existing legacy tests pass, plus a mixed current/legacy regression
proves the two populations remain separate.

### Step 5: Update scripts and documentation

Update documented export commands and `scripts/run-current-studies.sh` to pass
the checked release manifest. State that `export-site` is not an independent
validator; it invokes the canonical current-study and publication validators.

Do not regenerate website data as part of this plan unless the operator asks.

**Verify**: `python3 bench.py export-site --help` and documentation examples use
the same option name and path semantics.

## Test plan

Model new tests after `tests/test_export.py` existing temporary study/output
fixtures, but generate valid current studies through production study writers
where possible. Cover:

- current export requires manifest;
- eligible current study exports;
- ineligible current study fails atomically;
- wrong task set/digest fails;
- self-asserted configuration collision fails;
- legacy explicit compatibility remains supported;
- private-heldout and retired studies remain blocked;
- merge-existing runs only after all incoming studies validate.

## Done criteria

- [ ] Current-protocol website export requires a checked release manifest.
- [ ] Every current study passes the canonical validator and `check_publication` before grouping.
- [ ] Export failure leaves the destination unchanged.
- [ ] Legacy data remains explicit and cannot merge into current aggregates.
- [ ] Export and CLI tests pass.
- [ ] Site tests and build pass without changing UI behavior.
- [ ] Documentation and scripts show the release-manifest argument.
- [ ] No deployment or generated benchmark-data publication occurred.
- [ ] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- Plan 009's validator is absent or has a different API than assumed.
- Existing current website rows cannot be traced to a checked release manifest.
- Supporting existing rows would require silently labeling legacy data as
  current publication evidence.
- The change would require modifying site visualization semantics rather than
  only its data-production gate.

## Maintenance notes

Any future public output format—CSV, API, badges, or reports—should consume the
same validated publication object rather than raw study JSON. Reviewers should
look for grouping or aggregation before validation; that ordering recreates the
identity-mixing bug this plan removes.
