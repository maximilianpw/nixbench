final: prev: let
  muslPatch = ./overlay.nix;
in {
  tinygrep = prev.tinygrep.overrideAttrs (old: {
    version = "0.2.0";
    patches = (old.patches or []) ++ [muslPatch];
    doCheck = true;
    meta =
      (old.meta or {})
      // {
        broken = false;
      };
  });

  tinygrep-debug = final.tinygrep.overrideAttrs (old: {
    pname = "${old.pname}-debug";
    dontStrip = true;
  });
}
