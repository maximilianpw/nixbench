#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

mkdir -p "$tmpdir/modules/shared" "$tmpdir/dotfiles/config/hypr"
touch \
  "$tmpdir/modules/shared/tmux.nix" \
  "$tmpdir/modules/shared/lsp.nix" \
  "$tmpdir/modules/shared/zsh.nix" \
  "$tmpdir/dotfiles/config/hypr/common.conf" \
  "$tmpdir/dotfiles/config/hypr/keybind.conf"

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
  moduleRoots = {
    shared = $tmpdir/modules/shared;
    config = $tmpdir/dotfiles/config;
  };
  module = import ${workdir}/home.nix {
    inherit moduleRoots;
  };
  expectedImports = [
    "$tmpdir/modules/shared/tmux.nix"
    "$tmpdir/modules/shared/lsp.nix"
    "$tmpdir/modules/shared/zsh.nix"
  ];
  commonSource = module.home.file.".config/hypr/common.conf".source;
  keybindSource = module.home.file.".config/hypr/keybind.conf".source;
in {
  schema_version = 2;
  criteria = {
    "imports-paths" = passes (
      map toString module.imports == expectedImports
      && builtins.all builtins.pathExists module.imports
    );
    "home-file-paths" = passes (
      toString commonSource == "$tmpdir/dotfiles/config/hypr/common.conf"
      && toString keybindSource == "$tmpdir/dotfiles/config/hypr/keybind.conf"
      && builtins.pathExists commonSource && builtins.pathExists keybindSource
    );
    "import-names" = passes (module.passthru.importNames == [ "tmux" "lsp" "zsh" ]);
    "path-types" = passes (
      builtins.all (path: builtins.typeOf path == "path") module.imports
      && builtins.typeOf commonSource == "path"
      && builtins.typeOf keybindSource == "path"
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"imports-paths":false,"home-file-paths":false,"import-names":false,"path-types":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
