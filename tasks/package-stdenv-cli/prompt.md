# Package A stdenv CLI

Edit `package.nix`.

Write a `stdenv.mkDerivation` for a CLI named `tinygrep`.

Requirements:

- `pname = "tinygrep"` and `version = "0.1.0"`.
- Fetch from GitHub owner `nixbench`, repo `tinygrep`, rev `v${version}`.
- Use a non-empty fixed-output `hash`.
- Include `installShellFiles` in `nativeBuildInputs`.
- Use `makeFlags = [ "PREFIX=$(out)" ]`.
- Enable checks with `doCheck = true`.
- Install the binary to `$out/bin/tinygrep` in `installPhase`.
- Set `meta.description`, `meta.homepage`, `meta.license`, `meta.platforms`, and `meta.mainProgram`.
