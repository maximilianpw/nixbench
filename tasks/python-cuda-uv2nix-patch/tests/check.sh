#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  makePackage = name: marker: { inherit name marker; };
  makePath = name: marker: {
    outPath = "/nix/store/\${name}";
    __toString = self: self.outPath;
    inherit marker;
  };
  python = {
    sitePackages = "lib/python3.12/site-packages";
    pkgs = {
      buildPythonPackage = attrs: attrs // { __builder = "buildPythonPackage"; };
      hatchling = makePackage "hatchling" 157;
      torch = makePath "torch" 163;
      numpy = makePackage "numpy" 167;
    };
  };
  alternatePython = {
    sitePackages = "lib/python3.13/site-packages";
    pkgs = {
      buildPythonPackage = attrs: attrs // { __builder = "buildPythonPackage"; };
      hatchling = makePackage "alternate-hatchling" 191;
      torch = makePath "alternate-torch" 193;
      numpy = makePackage "alternate-numpy" 197;
    };
  };
  cudaPackages = {
    cudatoolkit = makePath "cuda-toolkit" 173;
    cudnn = makePath "cudnn" 179;
  };
  autoPatchelfHook = makePackage "autoPatchelfHook" 181;
  pkg = import ${workdir}/python-cuda.nix {
    inherit python cudaPackages autoPatchelfHook;
  };
  alternatePkg = import ${workdir}/python-cuda.nix {
    python = alternatePython;
    inherit cudaPackages autoPatchelfHook;
  };
  activeCode = text: builtins.concatStringsSep "\n" (
    builtins.filter
      (line:
        builtins.isString line
        && builtins.match "[[:space:]]*#.*" line == null)
      (builtins.split "\n" text)
  );
  phaseText = builtins.concatStringsSep "\n" (map (name: pkg.\${name} or "") [
    "preBuild"
    "prePatch"
    "postPatch"
    "preConfigure"
    "configurePhase"
    "postConfigure"
    "buildPhase"
    "postBuild"
    "preInstall"
    "installPhase"
    "postInstall"
    "preFixup"
    "postFixup"
    "preCheck"
    "checkPhase"
    "postCheck"
  ]);
in
assert pkg.__builder == "buildPythonPackage";
assert pkg.pname == "vision-trainer";
assert pkg.version == "0.1.0";
assert pkg.pyproject == true;
assert builtins.elem python.pkgs.hatchling pkg.nativeBuildInputs;
assert builtins.elem autoPatchelfHook pkg.nativeBuildInputs;
assert builtins.elem python.pkgs.torch pkg.propagatedBuildInputs;
assert builtins.elem python.pkgs.numpy pkg.propagatedBuildInputs;
assert builtins.elem alternatePython.pkgs.hatchling alternatePkg.nativeBuildInputs;
assert builtins.elem alternatePython.pkgs.torch alternatePkg.propagatedBuildInputs;
assert builtins.elem alternatePython.pkgs.numpy alternatePkg.propagatedBuildInputs;
assert builtins.elem cudaPackages.cudatoolkit pkg.buildInputs;
assert builtins.elem cudaPackages.cudnn pkg.buildInputs;
assert pkg.CUDA_HOME == cudaPackages.cudatoolkit;
assert builtins.match "(.|\n)*addAutoPatchelfSearchPath.*/nix/store/torch/lib/python3[.]12/site-packages/torch/lib(.|\n)*" (activeCode pkg.preFixup) != null;
assert builtins.match "(.|\n)*addAutoPatchelfSearchPath.*/nix/store/alternate-torch/lib/python3[.]13/site-packages/torch/lib(.|\n)*" (activeCode alternatePkg.preFixup) != null;
assert !(pkg ? LD_LIBRARY_PATH);
assert !((pkg.env or {}) ? LD_LIBRARY_PATH);
assert builtins.match "(.|\n)*/usr/local/cuda(.|\n)*" phaseText == null;
assert builtins.match "(.|\n)*pip[[:space:]]+install(.|\n)*" phaseText == null;
assert builtins.match "(.|\n)*LD_LIBRARY_PATH(.|\n)*" phaseText == null;
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
