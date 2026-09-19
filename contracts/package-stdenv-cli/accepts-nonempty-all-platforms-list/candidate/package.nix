{
  lib,
  stdenv,
  fetchFromGitHub,
  installShellFiles,
}:
stdenv.mkDerivation rec {
  pname = "tinygrep";
  version = "0.1.0";

  src = fetchFromGitHub {
    owner = "nixbench";
    repo = "tinygrep";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = [ installShellFiles ];

  makeFlags = [ "PREFIX=$(out)" ];

  doCheck = true;

  installPhase = ''
    runHook preInstall

    install -Dm755 tinygrep $out/bin/tinygrep

    runHook postInstall
  '';

  meta = {
    description = "A small grep-like command-line tool";
    homepage = "https://github.com/nixbench/tinygrep";
    license = lib.licenses.mit;
    platforms = lib.platforms.all;
    mainProgram = "tinygrep";
  };
}
