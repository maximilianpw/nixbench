import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { taskResults } from "@/data/benchmark";

const timingData = taskResults.map((task) => ({
  task: task.task
    .replace("debug-infinite-recursion", "debug recursion")
    .replace("devshell-tooling-contract", "dev shell")
    .replace("fetcher-source-pin", "fetcher pin")
    .replace("flake-per-system-outputs", "flake outputs")
    .replace("lang-attrsets-normalize", "attrsets")
    .replace("module-service-options", "module options")
    .replace("overlay-override-package", "overlay")
    .replace("package-python-application", "python app")
    .replace("package-stdenv-cli", "stdenv cli")
    .replace("purity-wrapper-derivation", "purity wrapper"),
  codex: task.codexSeconds,
  claude: task.claudeSeconds,
}));

function TimingTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
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
            <dd>{entry.value.toFixed(1)}s</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function TimingChart() {
  return (
    <div className="timing-chart react-timing-chart" role="img" aria-label="Task duration bars for Codex and Claude">
      <ResponsiveContainer width="100%" height={440}>
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
          <Bar dataKey="codex" name="Codex CLI" fill="var(--codex)" radius={0} />
          <Bar dataKey="claude" name="Claude CLI" fill="var(--claude)" radius={0} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
