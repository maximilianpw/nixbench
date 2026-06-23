#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  pkgs.bash = "/nix/store/bash";
  module = import ${workdir}/service.nix { inherit pkgs; };
  service = module.systemd.services.quote-runner.serviceConfig;
  exec = service.ExecStart;
in
assert service.Type == "oneshot";
assert service.StateDirectory == "quote-runner";
assert builtins.match ".*bash/bin/bash -lc.*" exec != null;
assert builtins.match ".*[$][{]NIXBENCH_MESSAGE[}].*" exec != null;
assert builtins.match ".*[$][{]STATE_DIRECTORY[}]/output[.]log.*" exec != null;
assert builtins.match ".*/usr/bin.*" exec == null;
assert builtins.match ".*/bin/sh.*" exec == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
