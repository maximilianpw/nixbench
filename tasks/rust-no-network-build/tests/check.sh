#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  lib.licenses.mit = "MIT";
  makePath = name: {
    outPath = "/nix/store/\${name}";
    __toString = self: self.outPath;
  };
  rustPlatform.buildRustPackage = attrs: attrs // { __builder = "buildRustPackage"; };
  fetchFromGitHub = attrs: attrs // { __fetcher = "github"; };
  fetchurl = attrs: attrs // makePath "vision-indexer-model";
  onnxruntime = makePath "onnxruntime";
  pkg = import ${workdir}/package.nix {
    inherit lib rustPlatform fetchFromGitHub fetchurl onnxruntime;
  };
  flags = builtins.concatStringsSep " " (pkg.cargoBuildFlags or []);
  envText = builtins.toJSON (pkg.env or {});
in
assert pkg.__builder == "buildRustPackage";
assert pkg.pname == "vision-indexer";
assert pkg.version == "0.4.0";
assert pkg.src.owner == "example";
assert pkg.src.repo == "vision-indexer";
assert pkg.src.rev == "v0.4.0";
assert pkg.cargoHash != "";
assert builtins.elem onnxruntime pkg.buildInputs;
assert builtins.match ".*download-binaries.*" flags == null;
assert builtins.match ".*--no-default-features.*" flags != null;
assert builtins.match ".*system-onnxruntime.*" flags != null;
assert pkg.env.ORT_STRATEGY == "system";
assert pkg.env.ORT_DYLIB_PATH == "/nix/store/onnxruntime/lib/libonnxruntime.so";
assert pkg.env.VISION_INDEXER_MODEL == "/nix/store/vision-indexer-model";
assert builtins.match ".*https://.*" envText == null;
assert pkg.passthru.assets.model.url == "https://models.example.invalid/vision-indexer/model-v1.onnx";
assert pkg.passthru.assets.model.hash == "sha256-model";
assert builtins.match ".*substituteInPlace.*download_model.*use_pinned_model.*" (pkg.postPatch or "") != null;
assert !(pkg ? __noChroot);
assert !(pkg ? allowSubstitutes);
assert pkg.meta.license == "MIT";
assert pkg.meta.mainProgram == "vision-indexer";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
