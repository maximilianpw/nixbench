{
  lib,
  stdenv,
  fetchFromGitHub,
  installShellFiles,
}:
stdenv.mkDerivation (finalAttrs: {
  pname = "tinygrep";
  version = "0.1.0";

  src = fetchFromGitHub {
    owner = "nixbench";
    repo = "tinygrep";
    rev = "v${finalAttrs.version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };

  nativeBuildInputs = [ installShellFiles ];

  makeFlags = [ "PREFIX=$(out)" ];

  doCheck = true;

  installPhase = ''
    runHook preInstall

    install -Dm755 tinygrep "$out/bin/tinygrep"

    runHook postInstall
  '';

  meta = {
    description = "Small command-line text search tool";
    homepage = "https://github.com/nixbench/tinygrep";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
    mainProgram = "tinygrep";
  };
})
