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
  fetchurl = attrs: attrs // makePath "vision-indexer-model" // { __fetcher = "url"; };
  onnxruntime = makePath "onnxruntime";
  pkg = import ${workdir}/package.nix {
    inherit lib rustPlatform fetchFromGitHub fetchurl onnxruntime;
  };
  flags = builtins.concatStringsSep " " (
    (pkg.cargoBuildFlags or []) ++ (pkg.cargoBuildFeatures or [])
  );
  envValues = builtins.attrValues (pkg.env or {}) ++ [
    (pkg.ORT_DYLIB_PATH or null)
    (pkg.ORT_LIB_LOCATION or null)
    (pkg.VISION_INDEXER_MODEL or null)
    (pkg.MODEL_PATH or null)
  ];
  envText = builtins.toJSON envValues;
  phaseText = builtins.concatStringsSep "\n" (map (name: pkg.\${name} or "") [
    "prePatch"
    "postPatch"
    "preConfigure"
    "configurePhase"
    "postConfigure"
    "preBuild"
    "buildPhase"
    "postBuild"
    "preInstall"
    "installPhase"
    "postInstall"
    "preFixup"
    "postFixup"
    "preCheck"
    "checkPhase"
    "postCheck"
  ]);
  phaseLines = builtins.filter builtins.isString (builtins.split "\n" phaseText);
  activePhaseLines = map (line: builtins.head (builtins.split "#" line)) phaseLines;
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
assert builtins.any (
  value:
    builtins.isString value
    && builtins.match "/nix/store/onnxruntime(/lib.*)?" value != null
) envValues;
assert builtins.any (
  value:
    builtins.isString value
    && builtins.match "/nix/store/vision-indexer-model(/.*)?" value != null
) envValues;
assert builtins.match ".*https?://.*" envText == null;
assert !(builtins.any (line: builtins.match ".*(curl|wget)([[:space:]]|$).*" line != null) activePhaseLines);
assert !(builtins.any (line: builtins.match ".*https?://.*" line != null) activePhaseLines);
assert pkg.passthru.assets.model.__fetcher == "url";
assert pkg.passthru.assets.model.url == "https://models.example.invalid/vision-indexer/model-v1.onnx";
assert builtins.isString pkg.passthru.assets.model.hash;
assert builtins.match "sha256-[A-Za-z0-9+/]{43}=" pkg.passthru.assets.model.hash != null;
assert !(pkg ? __noChroot);
assert !(pkg ? __darwinAllowLocalNetworking);
assert !(pkg ? sandbox);
assert pkg.meta.license == "MIT";
assert pkg.meta.mainProgram == "vision-indexer";
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
