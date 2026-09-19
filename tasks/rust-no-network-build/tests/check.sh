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
    licenses.mit = "MIT";
    getLib = package: package;
  };
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
in {
  schema_version = 2;
  criteria = {
    "package-source" = passes (
      pkg.__builder == "buildRustPackage" && pkg.pname == "vision-indexer"
      && pkg.version == "0.4.0" && pkg.src.owner == "example"
      && pkg.src.repo == "vision-indexer" && pkg.src.rev == "v0.4.0"
      && pkg.cargoHash != "" && pkg.meta.license == "MIT"
      && pkg.meta.mainProgram == "vision-indexer"
    );
    "system-onnxruntime" = passes (
      builtins.elem onnxruntime pkg.buildInputs
      && builtins.match ".*download-binaries.*" flags == null
      && builtins.any (value: builtins.isString value && builtins.match "/nix/store/onnxruntime(/lib.*)?" value != null) envValues
    );
    "pinned-model" = passes (
      builtins.any (value: builtins.isString value && builtins.match "/nix/store/vision-indexer-model(/.*)?" value != null) envValues
      && pkg.passthru.assets.model.__fetcher == "url"
      && pkg.passthru.assets.model.url == "https://models.example.invalid/vision-indexer/model-v1.onnx"
      && builtins.isString pkg.passthru.assets.model.hash
      && builtins.match "sha256-[A-Za-z0-9+/]{43}=" pkg.passthru.assets.model.hash != null
    );
    "no-network-escape" = passes (
      builtins.match ".*https?://.*" envText == null
      && !(builtins.any (line: builtins.match ".*(curl|wget)([[:space:]]|$).*" line != null) activePhaseLines)
      && !(builtins.any (line: builtins.match ".*https?://.*" line != null) activePhaseLines)
      && !(pkg ? __noChroot) && !(pkg ? __darwinAllowLocalNetworking) && !(pkg ? sandbox)
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"package-source":false,"system-onnxruntime":false,"pinned-model":false,"no-network-escape":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
