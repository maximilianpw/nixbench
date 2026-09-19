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
  lib = {
    licenses.mit = { spdxId = "MIT"; marker = 51; };
    platforms.unix = [ "unix-platform-sentinel" ];
    platforms.all = [ "all-platforms-sentinel" ];
  };
  stdenv.mkDerivation = definition:
    let attrs = if builtins.isFunction definition then definition attrs else definition;
    in attrs // { __mkDerivation = true; };
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
in {
  schema_version = 2;
  criteria = {
    "package-source" = passes (
      pkg.__mkDerivation == true && pkg.pname == "tinygrep" && pkg.version == "0.1.0"
      && pkg.src.owner == "nixbench" && pkg.src.repo == "tinygrep"
      && pkg.src.rev == "v0.1.0" && pkg.src.__fetcher == "github"
      && builtins.isString pkg.src.hash
      && builtins.match "sha256-[A-Za-z0-9+/]{43}=" pkg.src.hash != null
    );
    "build-contract" = passes (
      builtins.elem installShellFiles pkg.nativeBuildInputs
      && pkg.makeFlags == [ "PREFIX=\$(out)" ] && pkg.doCheck == true
    );
    "install-contract" = passes (
      builtins.match "(.|\n)*((install|cp|mv)[[:space:]][^\n]*tinygrep[^\n]*[$]out/bin/tinygrep|make[[:space:]]+install)(.|\n)*" installCode != null
    );
    "package-metadata" = passes (
      builtins.isString pkg.meta.description && pkg.meta.description != ""
      && builtins.isString pkg.meta.homepage && pkg.meta.homepage != ""
      && pkg.meta.license == lib.licenses.mit
      && builtins.isList pkg.meta.platforms && pkg.meta.platforms != []
      && pkg.meta.mainProgram == "tinygrep"
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"package-source":false,"build-contract":false,"install-contract":false,"package-metadata":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
