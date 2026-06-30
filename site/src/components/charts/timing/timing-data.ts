import { modelColors } from "@/components/charts/model-colors";
import { resultColumns, taskResults } from "@/data/benchmark";

export const timingData = taskResults.map((task) => {
  const row: Record<string, string | number | undefined> = {
    task: task.task
      .replace("container-native-vs-oci", "containers")
      .replace("debug-infinite-recursion", "debug recursion")
      .replace("debug-network-false-lead", "network false lead")
      .replace("devshell-tooling-contract", "dev shell")
      .replace("fetcher-source-pin", "fetcher pin")
      .replace("fhs-binary-wrapper", "fhs wrapper")
      .replace("flake-input-package-selection", "flake package")
      .replace("flake-per-system-outputs", "flake outputs")
      .replace("home-manager-extra-special-args", "hm extra args")
      .replace("home-manager-wsl-module-import", "hm wsl")
      .replace("home-manager-xdg-files", "hm xdg")
      .replace("issue-report-quality", "issue report")
      .replace("lang-attrsets-normalize", "attrsets")
      .replace("module-path-composition", "module paths")
      .replace("module-service-options", "module options")
      .replace("module-stale-option-migration", "stale option")
      .replace("module-system-boundaries", "module boundaries")
      .replace("mutable-config-home-manager", "mutable config")
      .replace("overlay-module-boundary", "overlay boundary")
      .replace("overlay-override-package", "overlay")
      .replace("package-name-lookup-contract", "package lookup")
      .replace("package-python-application", "python app")
      .replace("package-stdenv-cli", "stdenv cli")
      .replace("purity-wrapper-derivation", "purity wrapper")
      .replace("python-cuda-uv2nix-patch", "cuda patch")
      .replace("string-escaping-systemd", "string escaping"),
  };

  for (const column of resultColumns) {
    row[column.key] = task.results[column.key]?.seconds;
  }

  return row;
});

export { modelColors };
