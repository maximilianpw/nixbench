{
  stdenv,
  lib,
  makeWrapper,
  coreutils,
  bash,
}:
stdenv.mkDerivation {
  pname = "pure-runner";
  version = "1.0.0";

  nativeBuildInputs = [makeWrapper];

  installPhase = ''
    runHook preInstall
    mkdir -p $out/bin
    makeWrapper ${bash}/bin/bash $out/bin/pure-runner \
      --prefix PATH : ${lib.makeBinPath [coreutils]}
    runHook postInstall
  '';

  passthru.pure = true;
}
