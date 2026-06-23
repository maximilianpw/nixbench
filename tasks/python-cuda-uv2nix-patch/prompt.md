# Patch Python CUDA Package Inputs

Edit `python-cuda.nix`.

Package a Python application named `vision-trainer` using the provided fake Python and CUDA package sets.

Requirements:

- Use `python.pkgs.buildPythonPackage`.
- Set `pname = "vision-trainer"` and `version = "0.1.0"`.
- Set `pyproject = true`.
- Include `python.pkgs.hatchling` and `autoPatchelfHook` in `nativeBuildInputs`.
- Include `python.pkgs.torch` and `python.pkgs.numpy` in runtime Python inputs.
- Include `cudaPackages.cudatoolkit` and `cudaPackages.cudnn` in `buildInputs`.
- Set `CUDA_HOME = cudaPackages.cudatoolkit`.
- Add a `preFixup` that calls `addAutoPatchelfSearchPath` for `${python.pkgs.torch}/${python.sitePackages}/torch/lib`.
- Do not use `/usr/local/cuda`, `LD_LIBRARY_PATH`, `pip install`, or shell-only fixes.

## Source Context

This task is modeled after a NixOS Discourse uv2nix/CUDA guide where the author said ChatGPT/Gemini were not trustworthy for general NixOS, flakes, or Python-on-NixOS solutions, but could help identify package-providing libraries.

- NixOS Discourse: https://discourse.nixos.org/t/setting-deep-learning-python-project-with-cuda-support-using-uv2nix/72028
