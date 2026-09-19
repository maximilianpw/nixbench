# Choose Native NixOS Containers

Edit `container.nix`.

Define a native NixOS container named `ubuntu-lab`. Despite the name, this task is about the NixOS `containers` module, not Docker, Podman, or OCI image containers.

Requirements:

- Set `containers.ubuntu-lab.autoStart = true`.
- Set `containers.ubuntu-lab.privateNetwork = true`.
- Bind mount host `/dev/bus/usb` into the same path inside the container.
- The USB bind mount must not be read-only.
- Inside `containers.ubuntu-lab.config`, enable `services.openssh.enable`.
- `containers.ubuntu-lab.config` may be an attrset or a module function accepting `{ config, lib, pkgs, ... }`. The evaluator provides `pkgs.openssh`. Its `lib` argument implements `mkDefault` and `mkForce` as value wrappers and `mkIf` as a conditional attrset wrapper.
- Do not use `virtualisation.oci-containers`, `image`, `extraOptions`, or Docker/Podman-style device options.

## Source Context

This task is modeled after a Reddit report where ChatGPT mixed native NixOS containers with third-party backend containers while trying to configure an Ubuntu-like container with USB forwarding.

- Reddit: https://www.reddit.com/r/NixOS/comments/1ga6dbe/examples_of_questions_you_asked_an_llm_about_nix/
