{
  appimageTools,
  buildFHSUserEnv,
  fetchurl,
  pkgs,
}:
{
  environment.etc."ld.so.conf".text = "/usr/lib\n/lib\n";
  system.activationScripts.makeFhs = ''
    mkdir -p /usr/lib /lib /bin
    ln -s ${pkgs.glib}/lib/libglib.so /usr/lib/libglib.so
  '';
}
