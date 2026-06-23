{
  lib,
  python3Packages,
}:
python3Packages.buildPythonApplication rec {
  pname = "nixbench-report";
  version = "0.2.0";
  pyproject = true;

  src = ./.;

  nativeBuildInputs = [python3Packages.hatchling];
  propagatedBuildInputs = with python3Packages; [click rich];
  nativeCheckInputs = with python3Packages; [pytest];

  pythonImportsCheck = ["nixbench_report"];
  pytestFlagsArray = ["tests"];

  meta = {
    description = "Generate reports from NixBench results";
    homepage = "https://example.invalid/nixbench-report";
    license = lib.licenses.asl20;
    mainProgram = "nixbench-report";
  };
}
