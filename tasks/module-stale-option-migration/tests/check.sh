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
  module = import ${workdir}/module.nix {};
  cfg = if module ? config then module.config else module;
  oldXserver = cfg.services.xserver or {};
  oldDesktopManager = oldXserver.desktopManager or {};
in {
  schema_version = 2;
  criteria = {
    "sddm-current" = passes (
      cfg.services.displayManager.sddm.enable == true
      && !(oldXserver ? displayManager)
    );
    "plasma-current" = passes (
      cfg.services.desktopManager.plasma6.enable == true
      && !(oldDesktopManager ? plasma5)
    );
    "graphics-current" = passes (
      cfg.hardware.graphics.enable == true && !(cfg.hardware ? opengl)
    );
    "kdeconnect-no-stale" = passes (cfg.programs.kdeconnect.enable == true);
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"sddm-current":false,"plasma-current":false,"graphics-current":false,"kdeconnect-no-stale":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
