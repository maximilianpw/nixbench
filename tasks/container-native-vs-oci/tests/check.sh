#!/usr/bin/env sh
set -eu

workdir=${1:-$PWD}
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

cat > "$tmpdir/test.nix" <<EOF
let
  module = import ${workdir}/container.nix {};
  cfg = module.config;
  container = cfg.containers.ubuntu-lab;
in
assert !((cfg ? virtualisation) && (cfg.virtualisation ? oci-containers));
assert container.autoStart == true;
assert container.privateNetwork == true;
assert container.bindMounts."/dev/bus/usb".hostPath == "/dev/bus/usb";
assert container.bindMounts."/dev/bus/usb".isReadOnly == false;
assert container.config.services.openssh.enable == true;
assert !(container ? image);
assert !(container ? extraOptions);
"ok"
EOF

nix eval --json --file "$tmpdir/test.nix" >/dev/null
