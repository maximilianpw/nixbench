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

  nativeBuildInputs = [
    python.pkgs.hatchling
  ];

  propagatedBuildInputs = [
    python.pkgs.torch
  ];

  LD_LIBRARY_PATH = "/usr/local/cuda/lib64";

  installPhase = ''
    pip install .
  '';
}
