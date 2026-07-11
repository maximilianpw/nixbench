#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/modules/shared" "$tmpdir/dotfiles/config/hypr"
touch \
  "$tmpdir/modules/shared/tmux.nix" \
  "$tmpdir/modules/shared/lsp.nix" \
  "$tmpdir/modules/shared/zsh.nix" \
  "$tmpdir/dotfiles/config/hypr/common.conf" \
  "$tmpdir/dotfiles/config/hypr/keybind.conf"

cat > "$tmpdir/test.nix" <<EOF
let
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
in
assert map toString module.imports == expectedImports;
assert builtins.all (path: builtins.typeOf path == "path") module.imports;
assert builtins.all builtins.pathExists module.imports;
assert builtins.typeOf commonSource == "path";
assert builtins.typeOf keybindSource == "path";
assert toString commonSource == "$tmpdir/dotfiles/config/hypr/common.conf";
assert toString keybindSource == "$tmpdir/dotfiles/config/hypr/keybind.conf";
assert builtins.pathExists commonSource;
assert builtins.pathExists keybindSource;
assert module.passthru.importNames == [ "tmux" "lsp" "zsh" ];
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
