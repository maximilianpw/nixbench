#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makeModule = bash: import ${workdir}/service.nix { pkgs.bash = bash; };
  module = makeModule "/nix/store/nixbench-bash-primary";
  alternateModule = makeModule "/nix/store/nixbench-bash-alternate";
  service = module.systemd.services.quote-runner.serviceConfig;
  exec = service.ExecStart;
  alternateExec = alternateModule.systemd.services.quote-runner.serviceConfig.ExecStart;
  appendsWithRedirect =
    builtins.match ".*[$][{]NIXBENCH_MESSAGE[}][^;&|\n]*>>[^;&|\n]*[$][{]STATE_DIRECTORY[}]/output[.]log.*" exec != null;
  appendsWithTee =
    builtins.match ".*[$][{]NIXBENCH_MESSAGE[}][^;&\n]*[|][^;&\n]*tee[[:space:]]+(-a|--append)[^;&\n]*[$][{]STATE_DIRECTORY[}]/output[.]log.*" exec != null;
in
assert service.Type == "oneshot";
assert service.StateDirectory == "quote-runner";
assert builtins.match ".*/nix/store/nixbench-bash-primary/bin/bash -lc.*" exec != null;
assert builtins.match ".*/nix/store/nixbench-bash-alternate/bin/bash -lc.*" alternateExec != null;
assert builtins.match ".*[$][{]NIXBENCH_MESSAGE[}].*" exec != null;
assert builtins.match ".*[$][{]STATE_DIRECTORY[}]/output[.]log.*" exec != null;
assert appendsWithRedirect || appendsWithTee;
assert builtins.match ".*/usr/bin.*" exec == null;
assert builtins.match ".*/bin/sh.*" exec == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null

if sed 's/[[:space:]]*#.*$//' "$workdir/service.nix" \
  | grep -Eq "builtins[.]getEnv|[\"'](/usr/bin|/bin/sh)"; then
  echo "service.nix references a forbidden environment lookup or host shell" >&2
  exit 1
fi
