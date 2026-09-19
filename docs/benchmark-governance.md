# Benchmark governance

NixBench separates corpus roles because a public task and a held-out task
support different claims.

## Corpus roles

The public development corpus is fully inspectable. It supports local agent
development, evaluator audits, reproducible experiments, and diagnostic
comparisons. Public-corpus results must not be described as uncontaminated or
held out.

A private held-out corpus follows the same task, contract, rubric, release,
and reporting rules. It lives outside this repository and its Git history.
Operators may use it for stronger comparisons after the release and isolation
checks pass. Secrecy reduces direct exposure; it does not prove that task ideas
or equivalent material never appeared in training data.

A retired corpus contains former held-out tasks that no longer contribute to
active scores. After approval, operators publish retired prompts, starters,
references, evaluator history, and contract fixtures so others can audit them.

## Versions and immutable results

- A patch release changes documentation or harness code without changing task
  outcomes, scoring, or the required run protocol.
- A minor release adds tasks without changing existing task contracts. It has
  a new content digest and reports results under that identity.
- A major release changes a prompt, starter, evaluator acceptance boundary,
  rubric, points, or required protocol.

Historical trials are immutable. Reports never rewrite them or silently pool
different corpus digests or configuration IDs.

## Task lifecycle

Tasks move through `draft`, `calibrating`, `active`, `quarantined`,
`deprecated`, and `retired` states. Draft tasks are incomplete. Calibrating
tasks collect contract and empirical evidence. Active tasks contribute to
scores. A quarantined task does not contribute to headline scores until its
contract is repaired and recalibrated. Deprecated tasks remain identifiable
but do not enter new releases. Retired held-out tasks may move to the public
archive after disclosure approval.

The checked deprecation registry is `corpus/task-deprecations.toml`, and
`corpus/task-lifecycle.toml` records quarantine exclusions. Release checks
reject active tasks that appear in either list.

## Release requirements

`python3 bench.py release-check --corpus-root . --explain` evaluates the
machine-enforced rules. An active release requires:

- a valid content-addressed corpus manifest;
- categories from `corpus/category-vocabulary.toml`;
- full-score references and valid starter rejections;
- at least one independent passing and rejecting fixture for every task;
- fixture coverage for every required rubric criterion;
- deterministic repeated reference and representative fixture outcomes;
- no invalid release measurements or active known-issue skips;
- evaluator runtime below 80 percent of its declared timeout;
- a release note, deprecation records, and a checked release manifest;
- a declared protocol schema for later publication checks.

Release CI recomputes evidence. A cached health report is allowed only outside
CI and only when its corpus digest, scoring schema, reporting versions,
release-tool digest, and canonical evidence digest match.

`publication-check` handles run-specific rules. It requires a complete
configuration identity, completion attestation, criteria-v2 scoring, complete
valid trials, and the protocol schema named by the release manifest. A private
held-out study also requires the approved `linux-bwrap-v1` profile. The
release manifest fixes the adapter digest and expected namespace preflight
evidence. Every trial must carry matching completion evidence.

## Calibration and corpus balance

Before activation, reviewers record solve rate and uncertainty across at least
three materially different agent configurations with repeated trials when the
budget permits. They also review timeout and invalid-measurement rates,
discrimination when the sample permits it, common failure classes, evaluator
disputes, accepted valid alternatives, author difficulty, and empirical
difficulty. Model results do not automatically change author difficulty or
task status.

Reports show every category. Categories with fewer than five active tasks are
descriptive only. New work should prioritize independent fetcher, devshell,
purity, overlay, language, and debugging tasks to reduce module and package
dominance. Do not add near-duplicates merely to increase the task count, and do
not reweight headline scores to conceal corpus composition.

## Redacted publication

Active private-corpus publication uses a strict allowlist. Whole-corpus or
stratum outcomes require at least five active tasks and twenty valid
task-trial observations. If the whole corpus misses either threshold, the
bundle contains identity and method metadata plus
`insufficient_aggregation = true`. It contains no scores, pass/fail totals,
invalid counts, timeout counts, or subordinate strata.

Active private bundles never contain task IDs or hashes, prompts, filenames,
references, evaluator content, logs, diffs, agent logs, or per-task outcomes.
The authorized private storage location retains full artifacts.
The public site exporter refuses active private and retired study summaries.
Use the redacted publication command for approved held-out aggregate reports.

## Isolation policy

Held-out publication requires a trusted launcher, not a recorded profile name
or raw `--agent-cmd`. The approved Linux profile uses bubblewrap. It mounts the
copied workspace read-write at `/workspace`, creates a fresh home and `/tmp`,
mounts required system and Nix store paths read-only, and omits the repository,
corpus, evaluator, reference, results, host home, and Nix daemon socket. The
resolved network policy controls network namespace isolation. The outer trusted
launcher owns the status path and records preflight and completion evidence.

The preflight runs inside the namespace before the model command. A fixed
mount allowlist keeps repository, corpus, evaluator, result, and host-home
paths outside the namespace. The preflight checks that the Nix daemon socket
is absent, the workspace is writable, forbidden neutral mount points are
absent, and the workspace bind comes from the task-independent
`/tmp/nixbench-isolated-<random>/work` staging path. This keeps private task,
corpus, run, model, and configuration identities out of mount information.
The launcher copies a host agent executable to the separate neutral
`/tmp/nixbench-isolated-agent-<random>/agent` staging path before binding it.
The cleared inner command runs as
PID 1, so `/proc/1/environ` cannot expose the outer launcher's environment.
After the command exits, the runner
rejects workspace symlinks that resolve outside the workspace before it runs
the evaluator. Hosts without this adapter may run development corpora, but
their held-out results are not publishable.

## Rotation and disclosure

Review rotation for each major leaderboard cycle and whenever contamination
evidence appears. Do not replace tasks selectively because a favored
configuration failed. When practical, record retirement decisions before
inspecting new comparison results. No private corpus is permanently secret or
permanently valid.

After retirement, remove the tasks from active scoring and publish their full
history only with approval. Report a public/private score difference as a
possible contamination signal only when category composition and protocols
match. It is not proof of memorization.

The first private corpus cannot activate until its private plan records exact
task briefs, calibration configurations, repetition count, cost budget, and
objective activation and quarantine thresholds. The operator checklist is a
local planning artifact. Public automation must not create remotes, push,
deploy, or publish private material.

Create an empty template only at a path outside this repository:

```sh
python3 bench.py init-private-corpus \
  --public-repo-root . \
  --destination /authorized/private/nixbench-corpus
```

The command creates no task briefs, Git repository, remote, or publication.
