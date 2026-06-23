#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  python = {
    sitePackages = "lib/python3.12/site-packages";
    pkgs = {
      buildPythonPackage = attrs: attrs // { __builder = "buildPythonPackage"; };
      hatchling = "hatchling";
      torch = "/nix/store/torch";
      numpy = "numpy";
    };
  };
  cudaPackages = {
    cudatoolkit = "/nix/store/cuda-toolkit";
    cudnn = "/nix/store/cudnn";
  };
  autoPatchelfHook = "autoPatchelfHook";
  pkg = import ${workdir}/python-cuda.nix {
    inherit python cudaPackages autoPatchelfHook;
  };
in
assert pkg.__builder == "buildPythonPackage";
assert pkg.pname == "vision-trainer";
assert pkg.version == "0.1.0";
assert pkg.pyproject == true;
assert builtins.elem python.pkgs.hatchling pkg.nativeBuildInputs;
assert builtins.elem autoPatchelfHook pkg.nativeBuildInputs;
assert builtins.elem python.pkgs.torch pkg.propagatedBuildInputs;
assert builtins.elem python.pkgs.numpy pkg.propagatedBuildInputs;
assert builtins.elem cudaPackages.cudatoolkit pkg.buildInputs;
assert builtins.elem cudaPackages.cudnn pkg.buildInputs;
assert pkg.CUDA_HOME == cudaPackages.cudatoolkit;
assert builtins.match ".*addAutoPatchelfSearchPath.*/nix/store/torch/lib/python3[.]12/site-packages/torch/lib.*" pkg.preFixup != null;
assert !(pkg ? LD_LIBRARY_PATH);
assert builtins.match ".*/usr/local/cuda.*" (pkg.preFixup or "") == null;
assert builtins.match ".*pip install.*" (pkg.installPhase or "") == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
