import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { resultColumns, taskResults, type ModelKey } from "@/data/benchmark";

const modelColors: Record<ModelKey, string> = {
  gpt55: "var(--pass)",
  gpt54: "var(--codex)",
  gpt54Mini: "var(--cyan)",
  claudeOpus48: "var(--claude)",
};

const timingData = taskResults.map((task) => {
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
    row[column.key] = task.results[column.key].seconds;
  }

  return row;
});

function TimingTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value?: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>
      <dl>
        {payload.map((entry) => (
          <div key={entry.name}>
            <dt>{entry.name}</dt>
            <dd>{entry.value == null ? "--" : `${entry.value.toFixed(1)}s`}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function TimingChart() {
  return (
    <div className="timing-chart react-timing-chart" role="img" aria-label="Task duration bars for model runs">
      <ResponsiveContainer width="100%" height={760}>
        <BarChart data={timingData} layout="vertical" margin={{ top: 10, right: 24, bottom: 10, left: 12 }}>
          <CartesianGrid stroke="var(--grid-line)" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 240]}
            tickFormatter={(value) => `${value}s`}
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
          />
          <YAxis
            dataKey="task"
            type="category"
            width={138}
            stroke="var(--muted)"
            tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
          />
          <Tooltip content={<TimingTooltip />} cursor={{ fill: "color-mix(in srgb, var(--nix-blue) 6%, transparent)" }} />
          <Legend wrapperStyle={{ color: "var(--muted)", fontFamily: "var(--mono)", fontSize: "0.76rem" }} />
          {resultColumns.map((column) => (
            <Bar key={column.key} dataKey={column.key} name={column.label} fill={modelColors[column.key]} radius={0} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
