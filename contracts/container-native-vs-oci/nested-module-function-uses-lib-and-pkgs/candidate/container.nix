{ ... }:
{
  config.containers.ubuntu-lab = {
    autoStart = true;
    privateNetwork = true;
    bindMounts."/dev/bus/usb" = { hostPath = "/dev/bus/usb"; isReadOnly = false; };
    config = { lib, pkgs, ... }: {
      services.openssh.enable = lib.mkDefault true;
      environment.systemPackages = [ pkgs.openssh ];
    };
  };
}
