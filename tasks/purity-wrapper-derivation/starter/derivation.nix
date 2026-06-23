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

  installPhase = ''
    mkdir -p $out/bin
    echo '#!/usr/bin/env bash' > $out/bin/pure-runner
    echo 'echo ${builtins.getEnv "HOME"}' >> $out/bin/pure-runner
    chmod +x $out/bin/pure-runner
  '';
}
