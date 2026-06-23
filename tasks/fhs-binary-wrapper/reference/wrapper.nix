{
  appimageTools,
  buildFHSUserEnv,
  fetchurl,
  pkgs,
}:
{
  appimage = appimageTools.wrapType2 {
    pname = "vendor-tool";
    version = "2.0.0";
    src = fetchurl {
      url = "https://example.invalid/vendor-tool-2.0.0.AppImage";
      hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
    };
  };

  fhsEnv = buildFHSUserEnv {
    name = "vendor-tool-fhs";
    targetPkgs = pkgs: [
      pkgs.alsa-lib
      pkgs.glib
      pkgs.gtk3
    ];
    runScript = "vendor-tool";
  };
}
