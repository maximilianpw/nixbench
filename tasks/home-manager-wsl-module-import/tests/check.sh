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
  homeManagerModule = {
    module = "home-manager-nixos-module";
    marker = 103;
  };
  cfg = import ${workdir}/configuration.nix { inherit homeManagerModule; };
in {
  schema_version = 2;
  criteria = {
    "imports-module-argument" = passes (builtins.elem homeManagerModule cfg.imports);
    "wsl-config" = passes (
      cfg.wsl.enable == true && cfg.wsl.defaultUser == "nixos"
    );
    "home-manager-integration" = passes (
      cfg.home-manager.useGlobalPkgs == true
      && cfg.home-manager.useUserPackages == true
      && cfg.home-manager.users.nixos.programs.git.enable == true
    );
    "no-standalone-entrypoint" = passes (!(cfg ? homeConfiguration));
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"imports-module-argument":false,"wsl-config":false,"home-manager-integration":false,"no-standalone-entrypoint":false},"notes":[]}' >"$score_tmp"
fi
if sed 's/[[:space:]]*#.*$//' "$workdir/configuration.nix" | grep -Eq '<home-manager/nixos>|homeManagerConfiguration'; then
  python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); p["criteria"]["no-standalone-entrypoint"]=False; json.dump(p,open(sys.argv[1],"w"),separators=(",",":"))' "$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
