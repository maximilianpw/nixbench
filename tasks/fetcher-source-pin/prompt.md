# Pin A GitHub Source Fetcher

Edit `source.nix`.

Return a `fetchFromGitHub` source with:

- `owner = "nix-community"`.
- `repo = "nixbench-fixture"`.
- `rev` pinned to a commit-like 40-character lowercase hex string, not a branch name.
- A non-empty SRI hash beginning with `sha256-`.
- `fetchSubmodules = true`.
- `leaveDotGit = false`.
