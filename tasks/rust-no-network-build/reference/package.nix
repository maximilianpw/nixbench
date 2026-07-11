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
    owner = "example";
    repo = "vision-indexer";
    rev = "v${version}";
    hash = "sha256-source";
  };

  cargoHash = "sha256-cargo";

  buildInputs = [
    onnxruntime
  ];

  cargoBuildFlags = [
    "--no-default-features"
    "--features"
    "system-onnxruntime"
  ];

  env = {
    ORT_STRATEGY = "system";
    ORT_DYLIB_PATH = "${onnxruntime}/lib/libonnxruntime.so";
    VISION_INDEXER_MODEL = "${model}";
  };

  postPatch = ''
    substituteInPlace crates/model/build.rs \
      --replace-fail 'download_model()' 'use_pinned_model()'
  '';

  passthru.assets.model = model;

  meta = {
    description = "Index images with a small ONNX model";
    homepage = "https://example.invalid/vision-indexer";
    license = lib.licenses.mit;
    mainProgram = "vision-indexer";
  };
}
