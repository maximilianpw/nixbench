#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib = {
    licenses.mit = { spdxId = "MIT"; marker = 51; };
    platforms.unix = [ "unix-platform-sentinel" ];
  };
  stdenv.mkDerivation = attrs: attrs // { __mkDerivation = true; };
  fetchFromGitHub = attrs: attrs // { __fetcher = "github"; };
  installShellFiles = { package = "installShellFiles"; marker = 59; };
  pkg = import ${workdir}/package.nix {
    inherit lib stdenv fetchFromGitHub installShellFiles;
  };
  installCode = builtins.concatStringsSep "\n" (
    map
      (line:
        if builtins.isString line
        then builtins.head (builtins.split "#" line)
        else "")
      (builtins.split "\n" pkg.installPhase)
  );
in
assert pkg.__mkDerivation == true;
assert pkg.pname == "tinygrep";
assert pkg.version == "0.1.0";
assert pkg.src.owner == "nixbench";
assert pkg.src.repo == "tinygrep";
assert pkg.src.rev == "v0.1.0";
assert pkg.src.__fetcher == "github";
assert builtins.isString pkg.src.hash;
assert builtins.match "sha256-[A-Za-z0-9+/]{43}=" pkg.src.hash != null;
assert builtins.elem installShellFiles pkg.nativeBuildInputs;
assert pkg.makeFlags == [ "PREFIX=\$(out)" ];
assert pkg.doCheck == true;
assert builtins.match "(.|\n)*((install|cp|mv)[[:space:]][^\n]*tinygrep[^\n]*[$]out/bin/tinygrep|make[[:space:]]+install)(.|\n)*" installCode != null;
assert builtins.isString pkg.meta.description;
assert pkg.meta.description != "";
assert builtins.isString pkg.meta.homepage;
assert pkg.meta.homepage != "";
assert pkg.meta.license == lib.licenses.mit;
assert pkg.meta.platforms == lib.platforms.unix;
assert pkg.meta.mainProgram == "tinygrep";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
