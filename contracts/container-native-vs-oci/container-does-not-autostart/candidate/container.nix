{ ... }:
{
  config.containers.ubuntu-lab = {
    autoStart = false;
    privateNetwork = true;

    bindMounts."/dev/bus/usb" = {
      hostPath = "/dev/bus/usb";
      isReadOnly = false;
    };

    config = {
      services.openssh.enable = true;
    };
  };
}
