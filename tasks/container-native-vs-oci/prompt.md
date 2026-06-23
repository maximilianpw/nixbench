# Choose Native NixOS Containers

Edit `container.nix`.

Define a native NixOS container named `ubuntu-lab`. Despite the name, this task is about the NixOS `containers` module, not Docker, Podman, or OCI image containers.

Requirements:

- Set `containers.ubuntu-lab.autoStart = true`.
- Set `containers.ubuntu-lab.privateNetwork = true`.
- Bind mount host `/dev/bus/usb` into the same path inside the container.
- The USB bind mount must not be read-only.
- Inside `containers.ubuntu-lab.config`, enable `services.openssh.enable`.
- Do not use `virtualisation.oci-containers`, `image`, `extraOptions`, or Docker/Podman-style device options.

## Source Context

This task is modeled after a Reddit report where ChatGPT mixed native NixOS containers with third-party backend containers while trying to configure an Ubuntu-like container with USB forwarding.

- Reddit: https://www.reddit.com/r/NixOS/comments/1ga6dbe/examples_of_questions_you_asked_an_llm_about_nix/
