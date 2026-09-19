{
  python,
  cudaPackages,
  autoPatchelfHook,
  ...
}:
python.pkgs.buildPythonPackage {
  pname = "vision-trainer";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  nativeBuildInputs = [
    python.pkgs.hatchling
    autoPatchelfHook
  ];

  propagatedBuildInputs = [
    python.pkgs.numpy
    python.pkgs.torch
  ];

  buildInputs = [
    cudaPackages.cudatoolkit
    cudaPackages.cudnn
  ];

  CUDA_HOME = cudaPackages.cudatoolkit;

  preFixup = ''
    addAutoPatchelfSearchPath ${python.pkgs.torch}/${python.sitePackages}/torch/lib
  '';

  meta.mainProgram = "vision-trainer";
}
