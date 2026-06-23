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

  nativeBuildInputs = [installShellFiles];
  makeFlags = ["PREFIX=$(out)"];
  doCheck = true;

  installPhase = ''
    runHook preInstall
    install -Dm755 tinygrep $out/bin/tinygrep
    installShellCompletion --cmd tinygrep --bash completions/tinygrep.bash
    runHook postInstall
  '';

  meta = {
    description = "Small grep-like CLI used by NixBench";
    homepage = "https://example.invalid/tinygrep";
    license = lib.licenses.mit;
    platforms = lib.platforms.unix;
    mainProgram = "tinygrep";
  };
}
