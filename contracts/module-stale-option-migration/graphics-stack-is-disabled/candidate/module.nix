{ ... }:
{
  config = {
    services.displayManager.sddm.enable = true;
    services.desktopManager.plasma6.enable = true;
    hardware.graphics.enable = false;
    programs.kdeconnect.enable = true;
  };
}
