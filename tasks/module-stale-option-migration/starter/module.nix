{ ... }:
{
  config = {
    services.xserver.displayManager.sddm.enable = true;
    services.xserver.desktopManager.plasma5.enable = true;
    hardware.opengl.enable = true;
    programs.kdeconnect.enable = true;
  };
}
