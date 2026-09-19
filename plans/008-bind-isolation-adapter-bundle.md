# Plan 008: Bind trusted isolation claims to the complete adapter bundle

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update this plan's row in
> `plans/README.md` unless a reviewer told you they maintain the index.
>
> **Drift check (run first)**: `git diff --stat 189998c..HEAD -- nixbench/adapters.py nixbench/isolation.py nixbench/protocol.py nixbench/release.py scripts/bwrap-codex-agent.py launchers/linux-bwrap-v1.toml tests/test_protocol.py tests/test_release.py tests/test_codex_adapter.py docs/reproducibility.md docs/running-agents.md`
> If any in-scope file changed, compare the excerpts below against live code.
> Stop on a semantic mismatch.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `189998c`, 2026-09-19

## Why this matters

A trusted adapter's published SHA-256 currently covers only its launcher script.
The approved Bubblewrap launcher imports its security-critical namespace and
preflight behavior from `nixbench/isolation.py`, and its policy is also
represented in `launchers/linux-bwrap-v1.toml`. Those files can change without
changing the adapter digest or configuration identity. Held-out publication
must bind trust to the complete executable security boundary, not one entry
point file.

## Current state

- `nixbench/adapters.py:18-20` hashes only `self.executable`:

  ```python
  @property
  def sha256(self) -> str:
      return hashlib.sha256(self.executable.read_bytes()).hexdigest()
  ```

- `scripts/bwrap-codex-agent.py:15-22` imports the actual isolation behavior:

  ```python
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  from nixbench.isolation import (
      APPROVED_HELDOUT_PROFILE,
      APPROVED_PREFLIGHT_EVIDENCE,
      build_bubblewrap_command,
      read_isolation_preflight,
  )
  ```

- `nixbench/protocol.py:168-199` puts `adapter.sha256` into the controlled
  protocol and therefore into `configuration_id`.
- `nixbench/release.py:425-432` and `:538-541` compare study/manifest adapter
  identity against the same single-file digest.
- `nixbench/release.py:887-906` separately includes several harness files in a
  release-gate digest, but publication does not recompute that release gate and
  does not use it as the adapter identity.
- Hashing conventions use SHA-256 over deterministic bytes and prefix IDs such
  as `cfg-`; follow the canonical length-prefixed hashing approach in
  `nixbench/corpus.py` or `_hash_json` conventions rather than concatenating
  ambiguous byte strings.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Adapter/protocol tests | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_protocol tests.test_codex_adapter tests.test_release -v` | all tests pass when Bubblewrap is available |
| Python syntax | `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile bench.py nixbench/*.py scripts/*.py` | exit 0 |
| Release check | `CI=1 PYTHONDONTWRITEBYTECODE=1 python3 bench.py release-check --corpus-root . --json` | exit 0 after manifest regeneration required by changed gate identity |
| Diff sanity | `git diff --check` | exit 0 |

## Scope

**In scope**:
- `nixbench/adapters.py`
- `nixbench/isolation.py` only if a public bundle-file declaration belongs there
- `nixbench/protocol.py`
- `nixbench/release.py`
- `scripts/bwrap-codex-agent.py` only if imports/declarations must change
- `launchers/linux-bwrap-v1.toml`
- `tests/test_protocol.py`
- `tests/test_release.py`
- `tests/test_codex_adapter.py`
- `docs/reproducibility.md`
- `docs/running-agents.md`
- `corpus/releases/2.0.0.json` and `docs/releases/2.0.0.md` only if the repository's release policy permits regenerating the current unreleased worktree manifest; otherwise STOP and request a version decision.

**Out of scope**:
- Redesigning Bubblewrap mounts or credential delivery.
- Supporting arbitrary third-party adapter plugins.
- Hashing the Codex/model binary in this plan; Plan 009 handles broader study
  identity validation, while agent executable identity may need a later schema.
- Publishing or pushing release artifacts.

## Git workflow

- Suggested branch: `advisor/008-bind-isolation-adapter-bundle`
- Suggested commit: `fix: bind isolation adapter bundle identity`
- Do not push, publish, or create a release without authorization.

## Steps

### Step 1: Specify the adapter bundle identity

Extend `TrustedAdapter` with an explicit deterministic list of files whose
bytes define the adapter's behavior. For `codex-json-bwrap`, include at least:

- `scripts/bwrap-codex-agent.py`;
- `nixbench/isolation.py`;
- `launchers/linux-bwrap-v1.toml`.

Include `nixbench/adapters.py` only if its runtime behavior affects launcher
construction after the command is resolved. Avoid silently hashing the whole
repository: the bundle must be small, auditable, and security-relevant.

Define one canonical digest function with domain separation, stable
repo-relative path names, byte lengths, file bytes, and executable bits where
relevant. Keep the external field name compatible only if compatibility is
honest; otherwise add `agent_adapter_bundle_sha256` under a protocol schema
migration rather than changing the meaning of `agent_adapter_sha256` silently.

**Verify**: unit-test that changing any one bundle member changes the digest,
and changing an unrelated file does not.

### Step 2: Propagate the bundle digest through protocol identity

Update `resolve_protocol` so complete protocols include the bundle digest in
the controlled data hashed into `configuration_id`. Add explicit JSON fields
to `ResolvedProtocol`/metadata rather than relying on a hidden implementation
detail.

Tests must show:

- identical bundle bytes produce identical configuration IDs;
- altered `isolation.py` bytes produce a different bundle digest and
  configuration ID;
- the non-isolated `codex-json` adapter still has a deterministic identity;
- legacy protocol summaries are handled only through the existing explicit
  compatibility path.

**Verify**: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_protocol -v` → all pass.

### Step 3: Bind release manifests and publication checks

Update private-heldout `trusted_isolation` manifests to store the bundle digest.
`check_publication` must compare:

1. study metadata bundle digest;
2. current registered adapter bundle digest;
3. checked release manifest bundle digest.

All three must match. A launcher-script-only digest must not satisfy the new
schema. Add a test where only `nixbench/isolation.py` differs and publication is
rejected.

If this changes the release-manifest schema, increment the schema version and
add explicit compatibility handling. Do not reinterpret existing schema-1
manifests as though they had bundle identity.

**Verify**: focused release tests pass, including the new transitive-change
rejection.

### Step 4: Update documentation and release evidence

Document exactly which files belong to each adapter bundle and why. State that
adapter bundle identity covers harness-side isolation behavior, not model
provider identity or the external model binary.

Regenerate checked release evidence only after all tests pass. If the current
2.0.0 manifest is considered already published and immutable, STOP and request
whether this requires 2.0.1, 2.1.0, or 3.0.0 under governance rules.

**Verify**: release check recomputes evidence and either passes with the newly
approved manifest or fails only on the explicitly deferred version decision.

## Test plan

- Unit test canonical digest determinism.
- Mutation tests for launcher script, `isolation.py`, and launcher TOML.
- Negative publication test for a stale bundle digest.
- Positive held-out publication fixture with all three identities matching.
- Legacy manifest test proving old identities are not silently upgraded.
- Follow the synthetic release-manifest fixture patterns in
  `tests/test_release.py` and protocol identity patterns in
  `tests/test_protocol.py`.

## Done criteria

- [ ] Isolation code changes alter the trusted adapter identity.
- [ ] Configuration IDs include the complete adapter bundle identity.
- [ ] Private publication compares study, registry, and release-manifest bundle identities.
- [ ] Legacy manifests are rejected or handled through an explicit schema compatibility path.
- [ ] Focused protocol, adapter, and release tests pass.
- [ ] Python compilation and `git diff --check` pass.
- [ ] Documentation explains bundle contents and limitations.
- [ ] `plans/README.md` status row is updated.

## STOP conditions

Stop and report if:

- The fix requires silently changing the semantics of a published manifest field.
- The current 2.0.0 release is immutable and no version bump has been authorized.
- Bundle identity would require hashing provider-controlled remote code that is
  unavailable as local bytes.
- Tests reveal the approved launcher executes additional local modules not
  listed in this plan; report the complete dependency set before proceeding.

## Maintenance notes

Every new trusted adapter must declare its transitive local trust bundle.
Reviewers should reject adapters whose digest is only the entry point while
runtime behavior comes from imports, configuration files, shell helpers, or
external wrappers. Version the bundle format if canonicalization changes.
