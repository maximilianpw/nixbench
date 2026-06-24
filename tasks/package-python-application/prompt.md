# Package A Python Application

Edit `default.nix`.

Write a Python application package for `nixbench-report`.

Requirements:

- Use `python3Packages.buildPythonApplication`.
- `pname = "nixbench-report"` and `version = "0.2.0"`.
- Set `pyproject = true`.
- Use `hatchling` in `nativeBuildInputs`.
- Runtime dependencies: `click` and `rich`.
- Test dependency: `pytest`.
- Set `pythonImportsCheck = [ "nixbench_report" ]`.
- Set `pytestFlagsArray = [ "tests" ]`.
- Set useful `meta`, including `description`, `homepage`, `license = lib.licenses.asl20`, and `mainProgram = "nixbench-report"`.
