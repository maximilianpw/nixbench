#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
  makeModule = bash: import ${workdir}/service.nix { pkgs.bash = bash; };
  module = makeModule "/nix/store/nixbench-bash-primary";
  alternateModule = makeModule "/nix/store/nixbench-bash-alternate";
  service = module.systemd.services.quote-runner.serviceConfig;
  exec = service.ExecStart;
  alternateExec = alternateModule.systemd.services.quote-runner.serviceConfig.ExecStart;
  appendsWithRedirect =
    builtins.match ".*printf[^;&|\n]*>>[^;&|\n]*output[.]log.*" exec != null;
  appendsWithTee =
    builtins.match ".*printf[^;&\n]*[|][^;&\n]*tee[[:space:]]+(-a|--append)[^;&\n]*output[.]log.*" exec != null;
in {
  schema_version = 2;
  criteria = {
    "service-shape" = passes (service.Type == "oneshot" && service.StateDirectory == "quote-runner");
    "bash-package" = passes (
      builtins.match ".*/nix/store/nixbench-bash-primary/bin/bash -l?c.*" exec != null
      && builtins.match ".*/nix/store/nixbench-bash-alternate/bin/bash -l?c.*" alternateExec != null
    );
    "runtime-variables" = passes (
      builtins.match ".*[$][{]NIXBENCH_MESSAGE[}].*" exec != null
      && builtins.match ".*[$][{]STATE_DIRECTORY[}]/output[.]log.*" exec != null
    );
    "safe-append-and-purity" = passes (
      (appendsWithRedirect || appendsWithTee)
      && builtins.match ".*/usr/bin.*" exec == null
      && builtins.match ".*/bin/sh.*" exec == null
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"service-shape":false,"bash-package":false,"runtime-variables":false,"safe-append-and-purity":false},"notes":[]}' >"$score_tmp"
fi
if sed 's/[[:space:]]*#.*$//' "$workdir/service.nix" | grep -Eq "builtins[.]getEnv|[\"'](/usr/bin|/bin/sh)"; then
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); p["criteria"]["safe-append-and-purity"]=False; json.dump(p,open(sys.argv[1],"w"),separators=(",",":"))' "$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
