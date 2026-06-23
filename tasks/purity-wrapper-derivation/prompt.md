# Pure Wrapper Derivation

Edit `derivation.nix`.

The starter uses host paths and environment variables. Rewrite it as a pure wrapper derivation.

Requirements:

- Use `stdenv.mkDerivation`.
- `pname = "pure-runner"` and `version = "1.0.0"`.
- Include `makeWrapper` in `nativeBuildInputs`.
- Do not reference `/usr/bin`, `/bin`, `$HOME`, or `builtins.getEnv`.
- Use the provided `bash` package as the wrapped executable.
- Build `PATH` with `lib.makeBinPath [ coreutils ]`.
- Set `passthru.pure = true`.
