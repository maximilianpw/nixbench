#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makePkg = attrs: attrs // {
    overrideAttrs = f:
      let
        next = attrs // f attrs;
      in
      makePkg next;
  };
  overlay = import ${workdir}/overlay.nix;
  base = {
    tinygrep = makePkg {
      pname = "tinygrep";
      version = "0.1.0";
      patches = [ ./existing.patch ];
      doCheck = false;
      meta = {
        description = "tiny grep";
        broken = true;
      };
    };
  };
  final = base // result;
  result = overlay final base;
in
assert result.tinygrep.version == "0.2.0";
assert result.tinygrep.doCheck == true;
assert builtins.length result.tinygrep.patches == 2;
assert result.tinygrep.meta.description == "tiny grep";
assert result.tinygrep.meta.broken == false;
assert result.tinygrep-debug.pname == "tinygrep-debug";
assert result.tinygrep-debug.version == "0.2.0";
assert result.tinygrep-debug.dontStrip == true;
"ok"
EOF

touch "$tmpdir/existing.patch"
nix eval --json --file "$tmpdir/test.nix" >/dev/null
