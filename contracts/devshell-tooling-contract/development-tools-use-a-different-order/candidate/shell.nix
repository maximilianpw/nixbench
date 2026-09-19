{
  mkShell,
  nixfmt-rfc-style,
  statix,
  deadnix,
  nil,
  alejandra ? null,
}:
mkShell {
  name = "nixbench-dev";

  packages =
    [
      nil
      deadnix
      statix
      nixfmt-rfc-style
    ]
    ++ (
      if alejandra == null
      then []
      else [alejandra]
    );

  NIXBENCH_FORMATTER = "nixfmt-rfc-style";

  shellHook = ''
    export NIX_CONFIG="experimental-features = flakes nix-command"
  '';
}
