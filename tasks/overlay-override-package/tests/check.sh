#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makePkg = attrs: attrs // {
    __overrideCount = attrs.__overrideCount or 0;
    overrideAttrs = f:
      let
        next = attrs // f attrs;
      in
      makePkg (next // {
        __overrideCount = (attrs.__overrideCount or 0) + 1;
      });
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
        homepage = "https://example.invalid/tinygrep";
        broken = true;
      };
    };
  };
  final = base // result // {
    tinygrep = makePkg (result.tinygrep // { __fromFinal = 151; });
  };
  result = overlay final base;
in
assert result.tinygrep.version == "0.2.0";
assert result.tinygrep.doCheck == true;
assert result.tinygrep.patches == [ ./existing.patch ${workdir}/fix-musl.patch ];
assert result.tinygrep.meta.description == "tiny grep";
assert result.tinygrep.meta.homepage == "https://example.invalid/tinygrep";
assert result.tinygrep.meta.broken == false;
assert result.tinygrep.__overrideCount == 1;
assert result.tinygrep-debug.pname == "tinygrep-debug";
assert result.tinygrep-debug.version == "0.2.0";
assert result.tinygrep-debug.dontStrip == true;
assert result.tinygrep-debug.patches == result.tinygrep.patches;
assert result.tinygrep-debug.doCheck == result.tinygrep.doCheck;
assert result.tinygrep-debug.meta == result.tinygrep.meta;
assert result.tinygrep-debug.__overrideCount == 2;
assert result.tinygrep-debug.__fromFinal == 151;
"ok"
EOF

touch "$tmpdir/existing.patch"
nix eval --json --file "$tmpdir/test.nix" >/dev/null
