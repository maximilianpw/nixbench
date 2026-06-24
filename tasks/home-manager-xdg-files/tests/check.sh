#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  home = import ${workdir}/home.nix {
    homeDirectory = "/home/alice";
    configText = "theme = \"dark\"\n";
  };
  text = builtins.toJSON home;
in
assert home.xdg.userDirs.enable == true;
assert home.xdg.userDirs.createDirectories == true;
assert home.xdg.userDirs.documents == "/home/alice/Documents";
assert home.xdg.userDirs.download == "/home/alice/Downloads";
assert home.xdg.configFile."nixbench/app.toml".text == "theme = \"dark\"\n";
assert home.home.file."GitHub_Repos/.keep".text == "";
assert !(home.home ? activation);
assert builtins.match ".*mkdir.*" text == null;
assert builtins.match ".*ln -s.*" text == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
