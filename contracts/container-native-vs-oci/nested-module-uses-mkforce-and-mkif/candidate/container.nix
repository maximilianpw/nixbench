{ ... }:
{
  config.containers.ubuntu-lab = {
    autoStart = true;
    privateNetwork = true;
    bindMounts."/dev/bus/usb" = { hostPath = "/dev/bus/usb"; isReadOnly = false; };
    config = { lib, pkgs, ... }:
      lib.mkIf true {
        services.openssh.enable = lib.mkForce true;
        environment.systemPackages = [ pkgs.openssh ];
      };
  };
}
