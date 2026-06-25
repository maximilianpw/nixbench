import { type CSSProperties, useMemo, useState } from "react";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { leaderboardRuns, formatMinutes, type LeaderboardRun } from "@/data/benchmark";

type ChartMode = "score" | "time" | "failures";

type ChartPoint = LeaderboardRun & {
  agentMinutes: number;
  label: string;
  color: string;
};

const chartModes: Record<
  ChartMode,
  {
    label: string;
    xKey: keyof ChartPoint;
    yKey: keyof ChartPoint;
    xLabel: string;
    yLabel: string;
    xDomain: [number, number];
    yDomain: [number, number];
    xTicks: number[];
    yTicks: number[];
    xFormatter: (value: number) => string;
    yFormatter: (value: number) => string;
  }
> = {
  score: {
    label: "NixBench pass rate plotted against agent time",
    xKey: "agentMinutes",
    yKey: "passRate",
    xLabel: "Agent minutes",
    yLabel: "Pass rate",
    xDomain: [0, 40],
    yDomain: [0, 100],
    xTicks: [0, 10, 20, 30, 40],
    yTicks: [25, 50, 75, 100],
    xFormatter: (value) => `${value}m`,
    yFormatter: (value) => `${value}%`,
  },
  time: {
    label: "NixBench agent time plotted against pass rate",
    xKey: "passRate",
    yKey: "agentMinutes",
    xLabel: "Pass rate",
    yLabel: "Agent minutes",
    xDomain: [0, 100],
    yDomain: [0, 40],
    xTicks: [0, 25, 50, 75, 100],
    yTicks: [0, 10, 20, 30, 40],
    xFormatter: (value) => `${value}%`,
    yFormatter: (value) => `${value}m`,
  },
  failures: {
    label: "NixBench failure count plotted against pass rate",
    xKey: "failed",
    yKey: "passRate",
    xLabel: "Failed tasks",
    yLabel: "Pass rate",
    xDomain: [0, 8],
    yDomain: [0, 100],
    xTicks: [0, 2, 4, 6, 8],
    yTicks: [25, 50, 75, 100],
    xFormatter: (value) => String(value),
    yFormatter: (value) => `${value}%`,
  },
};

function buildChartPoint(run: LeaderboardRun): ChartPoint {
  const colors: Record<string, string> = {
    "gpt-55": "var(--pass)",
    "gpt-54": "var(--codex)",
    "gpt-54-mini": "var(--cyan)",
    "claude-opus-48": "var(--claude)",
  };

  return {
    ...run,
    agentMinutes: formatMinutes(run.agentTimeSeconds),
    label: `${run.agent} · ${run.passRate}%`,
    color: colors[run.id] ?? (run.current ? "var(--pass)" : `var(--${run.kind})`),
  };
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartPoint }> }) {
  if (!active || !payload?.length) {
    return null;
  }

  const run = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>{run.agent}</strong>
      <span>{run.corpus}</span>
      <dl>
        <div>
          <dt>Pass@1</dt>
          <dd>{run.passRate}%</dd>
        </div>
        <div>
          <dt>Agent time</dt>
          <dd>{run.agentTimeLabel}</dd>
        </div>
        <div>
          <dt>Failed</dt>
          <dd>{run.failed}</dd>
        </div>
        <div>
          <dt>Tasks</dt>
          <dd>
            {run.completedTasks}/{run.totalTasks}
          </dd>
        </div>
      </dl>
    </div>
  );
}

export function LeaderboardPanel() {
  const [mode, setMode] = useState<ChartMode>("score");
  const chartData = useMemo(() => leaderboardRuns.map(buildChartPoint), []);
  const config = chartModes[mode];

  return (
    <section className="section leaderboard-section" id="leaderboard" aria-labelledby="leaderboard-heading">
      <div className="section-heading compact">
        <h2 id="leaderboard-heading">Leaderboard</h2>
      </div>

      <div className="leaderboard-panel">
        <div className="control-bar" aria-label="Leaderboard controls">
          <div className="control-groups">
            <ToggleGroup type="single" value="v0.2" aria-label="Corpus version">
              <ToggleGroupItem value="v0.2" aria-label="Corpus v0.2">
                v0.2
              </ToggleGroupItem>
              <ToggleGroupItem value="v0.1" aria-label="Corpus v0.1">
                v0.1
              </ToggleGroupItem>
            </ToggleGroup>
            <ToggleGroup
              type="single"
              value={mode}
              onValueChange={(value) => {
                if (value) setMode(value as ChartMode);
              }}
              aria-label="Chart metric"
            >
              <ToggleGroupItem value="score" aria-label="Show score">
                Score
              </ToggleGroupItem>
              <ToggleGroupItem value="time" aria-label="Show agent time">
                Agent time
              </ToggleGroupItem>
              <ToggleGroupItem value="failures" aria-label="Show failures">
                Failures
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
          <div className="leaderboard-meta">
            <span>
              <strong>24 tasks</strong> · updated <strong>June 24, 2026</strong>
            </span>
            <button className="filter-button" type="button">
              Runs <span>(4/4)</span>
            </button>
          </div>
        </div>

        <div className="score-plot react-chart-frame" role="img" aria-label={config.label}>
          <div className="plot-title">NixBench score</div>
          <span className="plot-note">higher pass rate is better</span>
          <div className="chart-shell">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 48, right: 56, bottom: 42, left: 34 }}>
                <CartesianGrid stroke="var(--grid-line)" strokeDasharray="0" />
                <XAxis
                  dataKey={config.xKey as string}
                  domain={config.xDomain}
                  tickFormatter={config.xFormatter}
                  ticks={config.xTicks}
                  type="number"
                  label={{ value: config.xLabel, position: "insideBottomRight", offset: -18 }}
                  stroke="var(--muted)"
                  tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
                />
                <YAxis
                  dataKey={config.yKey as string}
                  domain={config.yDomain}
                  tickFormatter={config.yFormatter}
                  ticks={config.yTicks}
                  type="number"
                  label={{ value: config.yLabel, position: "insideTopLeft", offset: -26 }}
                  stroke="var(--muted)"
                  tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
                />
                <ZAxis range={[120, 180]} />
                <Tooltip cursor={{ stroke: "var(--border-strong)" }} content={<ChartTooltip />} />
                {chartData.map((entry) => (
                  <Scatter
                    key={entry.id}
                    data={[entry]}
                    fill={entry.color}
                    name={entry.label}
                    stroke="var(--panel)"
                    strokeWidth={2}
                  />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend" aria-hidden="true">
            {chartData.map((run) => (
              <span key={run.id}>
                <i style={{ "--swatch": run.color } as CSSProperties} />
                {run.label}
              </span>
            ))}
          </div>
        </div>

        <div className="leaderboard-table-wrap">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th scope="col">Run</th>
                <th scope="col">Pass@1</th>
                <th scope="col">Score</th>
                <th scope="col">Agent time</th>
                <th scope="col">Failed</th>
              </tr>
            </thead>
            <tbody>
              {leaderboardRuns.map((run) => (
                <tr key={run.id}>
                  <th scope="row">
                    <span className="agent-cell">
                      <span className={`agent-mark ${run.kind}`} aria-hidden="true">
                        {run.marker}
                      </span>
                      <span>
                        <strong>{run.agent}</strong>
                        <small>
                          {run.corpus} · {run.runId}
                        </small>
                      </span>
                    </span>
                  </th>
                  <td>
                    <span className="score-percent">{run.passRate}%</span>
                    <span className="mini-bar">
                      <span style={{ width: `${run.passRate}%` }} />
                    </span>
                  </td>
                  <td>
                    {run.score} / {run.maxScore}
                  </td>
                  <td>{run.agentTimeLabel}</td>
                  <td>
                    {run.failed}
                    <small className="task-count-note">
                      {run.completedTasks}/{run.totalTasks}
                    </small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="source-note">
          Current rows are local artifacts from <code>results/</code>. The model comparison is summarized in{" "}
          <a href="docs/runs/2026-06-24-model-comparison.md">run notes</a>.
        </p>
      </div>
    </section>
  );
}
