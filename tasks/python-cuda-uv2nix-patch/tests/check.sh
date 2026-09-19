#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
command -v nix >/dev/null 2>&1 || exit 2
command -v python3 >/dev/null 2>&1 || exit 2

cat > "$tmpdir/test.nix" <<EOF
let
  passes = value:
    let attempt = builtins.tryEval (builtins.deepSeq value value);
    in attempt.success && attempt.value == true;
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
  runtimeInputs = package:
    (package.dependencies or []) ++ (package.propagatedBuildInputs or []);
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
in {
  schema_version = 2;
  criteria = {
    "package-identity" = passes (
      pkg.__builder == "buildPythonPackage" && pkg.pname == "vision-trainer"
      && pkg.version == "0.1.0" && pkg.pyproject == true
    );
    "python-inputs" = passes (
      builtins.elem python.pkgs.hatchling pkg.nativeBuildInputs
      && builtins.elem autoPatchelfHook pkg.nativeBuildInputs
      && builtins.elem python.pkgs.torch (runtimeInputs pkg)
      && builtins.elem python.pkgs.numpy (runtimeInputs pkg)
      && builtins.elem alternatePython.pkgs.hatchling alternatePkg.nativeBuildInputs
      && builtins.elem alternatePython.pkgs.torch (runtimeInputs alternatePkg)
      && builtins.elem alternatePython.pkgs.numpy (runtimeInputs alternatePkg)
    );
    "cuda-inputs" = passes (
      builtins.elem cudaPackages.cudatoolkit pkg.buildInputs
      && builtins.elem cudaPackages.cudnn pkg.buildInputs
      && pkg.CUDA_HOME == cudaPackages.cudatoolkit
    );
    "patchelf-and-pure-phases" = passes (
      builtins.match "(.|\n)*addAutoPatchelfSearchPath.*/nix/store/torch/lib/python3[.]12/site-packages/torch/lib(.|\n)*" (activeCode pkg.preFixup) != null
      && builtins.match "(.|\n)*addAutoPatchelfSearchPath.*/nix/store/alternate-torch/lib/python3[.]13/site-packages/torch/lib(.|\n)*" (activeCode alternatePkg.preFixup) != null
      && !(pkg ? LD_LIBRARY_PATH) && !((pkg.env or {}) ? LD_LIBRARY_PATH)
      && builtins.match "(.|\n)*/usr/local/cuda(.|\n)*" phaseText == null
      && builtins.match "(.|\n)*pip[[:space:]]+install(.|\n)*" phaseText == null
      && builtins.match "(.|\n)*LD_LIBRARY_PATH(.|\n)*" phaseText == null
    );
  };
  notes = [];
}
EOF

score_tmp="$NIXBENCH_SCORE_FILE.tmp.$$"
if ! nix eval --json --file "$tmpdir/test.nix" >"$score_tmp"; then
  printf '%s\n' '{"schema_version":2,"criteria":{"package-identity":false,"python-inputs":false,"cuda-inputs":false,"patchelf-and-pure-phases":false},"notes":[]}' >"$score_tmp"
fi
mv "$score_tmp" "$NIXBENCH_SCORE_FILE"
python3 "$NIXBENCH_EVALUATOR_EXIT" "$NIXBENCH_TASK_DIR/metadata.toml" "$NIXBENCH_SCORE_FILE"
