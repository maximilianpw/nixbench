final: prev: let
  compatibilityPatch = ./fix-musl.patch;
in {
  tinygrep = prev.tinygrep.overrideAttrs (old: {
    version = "0.2.0";
    patches = (old.patches or []) ++ [compatibilityPatch];
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
