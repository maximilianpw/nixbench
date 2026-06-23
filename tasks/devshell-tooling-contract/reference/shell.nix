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
      nixfmt-rfc-style
      statix
      deadnix
      nil
    ]
    ++ (
      if alejandra == null
      then []
      else [alejandra]
    );

  NIXBENCH_FORMATTER = "nixfmt-rfc-style";

  shellHook = ''
    export NIX_CONFIG="experimental-features = nix-command flakes"
  '';
}
