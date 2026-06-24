{ ... }:
{
  config = {
    services.displayManager.sddm.enable = true;
    services.desktopManager.plasma6.enable = true;
    hardware.graphics.enable = true;
    programs.kdeconnect.enable = true;
  };
}
