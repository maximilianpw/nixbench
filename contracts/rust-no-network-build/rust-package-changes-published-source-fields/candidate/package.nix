{
  lib,
  rustPlatform,
  fetchFromGitHub,
  fetchurl,
  onnxruntime,
}:

let
  model = fetchurl {
    url = "https://models.example.invalid/vision-indexer/model-v1.onnx";
    hash = "sha256-CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC=";
  };
in
rustPlatform.buildRustPackage rec {
  pname = "vision-indexer";
  version = "0.4.0";
  src = fetchFromGitHub {
    owner = "different";
    repo = "vision-indexer";
    rev = "v${version}";
    hash = "sha256-source";
  };
  cargoHash = "sha256-cargo";
  buildInputs = [ onnxruntime ];
  cargoBuildFlags = [ "--no-default-features" "--features" "system-onnxruntime" ];
  env = {
    ORT_DYLIB_PATH = "${onnxruntime}/lib/libonnxruntime.so";
    VISION_INDEXER_MODEL = "${model}";
  };
  passthru.assets.model = model;
  meta = {
    license = lib.licenses.mit;
    mainProgram = "vision-indexer";
  };
}
