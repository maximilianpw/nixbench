{ ... }:
{
  config.virtualisation.oci-containers.containers.ubuntu-lab = {
    image = "ubuntu:24.04";
    autoStart = true;
    extraOptions = [
      "--device=/dev/bus/usb:/dev/bus/usb"
    ];
  };
}
