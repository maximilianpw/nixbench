{
  lib,
  rustPlatform,
  fetchFromGitHub,
  fetchurl,
  onnxruntime,
}:

rustPlatform.buildRustPackage rec {
  pname = "vision-indexer";
  version = "0.4.0";

  src = fetchFromGitHub {
    owner = "example";
    repo = "vision-indexer";
    rev = "v${version}";
    hash = "sha256-source";
  };

  cargoHash = "sha256-cargo";

  cargoBuildFlags = [
    "--features"
    "download-binaries"
  ];

  env = {
    ORT_STRATEGY = "download";
    MODEL_URL = "https://models.example.invalid/vision-indexer/model-v1.onnx";
  };

  meta = {
    description = "Index images with a small ONNX model";
    homepage = "https://example.invalid/vision-indexer";
    license = lib.licenses.mit;
    mainProgram = "vision-indexer";
  };
}
