#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  aliceHome = import ${workdir}/home.nix {
    homeDirectory = "/home/alice";
    configText = "theme = \"dark\"\n";
  };
  bobHome = import ${workdir}/home.nix {
    homeDirectory = "/srv/users/bob";
    configText = "theme = \"light\"\nfont = \"mono\"\n";
  };
  validHome = homeDirectory: configText: home:
    let
      text = builtins.toJSON home;
    in
      home.xdg.userDirs.enable == true
      && home.xdg.userDirs.createDirectories == true
      && home.xdg.userDirs.documents == "\${homeDirectory}/Documents"
      && home.xdg.userDirs.download == "\${homeDirectory}/Downloads"
      && home.xdg.configFile."nixbench/app.toml".text == configText
      && home.home.file ? "GitHub_Repos/.keep"
      && home.home.file."GitHub_Repos/.keep" ? text
      && builtins.isString home.home.file."GitHub_Repos/.keep".text
      && !(home.home ? activation)
      && builtins.match ".*mkdir.*" text == null
      && builtins.match ".*ln -s.*" text == null;
in
assert validHome "/home/alice" "theme = \"dark\"\n" aliceHome;
assert validHome "/srv/users/bob" "theme = \"light\"\nfont = \"mono\"\n" bobHome;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
