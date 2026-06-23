#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib = {
    licenses.mit = "MIT";
    platforms.unix = [ "x86_64-linux" "aarch64-darwin" ];
  };
  stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
  fetchFromGitHub = attrs: attrs // { __fetcher = "github"; };
  installShellFiles = "installShellFiles";
  pkg = import ${workdir}/package.nix {
    inherit lib stdenv fetchFromGitHub installShellFiles;
  };
in
assert pkg.__mkDerivation == true;
assert pkg.pname == "tinygrep";
assert pkg.version == "0.1.0";
assert pkg.src.owner == "nixbench";
assert pkg.src.repo == "tinygrep";
assert pkg.src.rev == "v0.1.0";
assert pkg.src.hash != "";
assert builtins.elem installShellFiles pkg.nativeBuildInputs;
assert pkg.makeFlags == [ "PREFIX=\$(out)" ];
assert pkg.doCheck == true;
assert builtins.match ".*out/bin/tinygrep.*" pkg.installPhase != null;
assert pkg.meta.license == "MIT";
assert pkg.meta.mainProgram == "tinygrep";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
