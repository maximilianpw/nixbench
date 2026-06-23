{
  allSystems ? ["x86_64-linux" "aarch64-linux" "aarch64-darwin"],
  defaultSystem ? "x86_64-linux",
}: packages:
# TODO: Normalize the package attrset as described in NIXBENCH_PROMPT.md.
{
  inherit defaultSystem;
  names = [];
  versions = {};
  bySystem = {};
  defaultPackages = [];
}
