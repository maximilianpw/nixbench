{ lib, python3Packages }:
python3Packages.buildPythonApplication {
  pname = "nixbench-report"; version = "0.2.0"; pyproject = true; src = ./.;
  nativeBuildInputs = [ python3Packages.hatchling ]; dependencies = []; propagatedBuildInputs = [];
  nativeCheckInputs = [ python3Packages.pytest python3Packages.click python3Packages.rich ];
  pythonImportsCheck = [ "nixbench_report" ]; pytestFlagsArray = [ "tests" ];
  meta = { description = "Generate reports"; homepage = "https://example.invalid/report"; license = lib.licenses.asl20; mainProgram = "nixbench-report"; };
}
