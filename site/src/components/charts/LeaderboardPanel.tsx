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
import { leaderboardRuns, formatMinutes, type LeaderboardRun, type ModelKey } from "@/data/benchmark";

type ChartMode = "score" | "time" | "failures";

type ChartPoint = LeaderboardRun & {
  agentMinutes: number;
  label: string;
  color: string;
};

type ChartSeries = {
  key: ModelKey;
  label: string;
  color: string;
  points: ChartPoint[];
};

const effortOrder = {
  low: 0,
  medium: 1,
  high: 2,
  xhigh: 3,
} as const;

const seriesColors: Record<ModelKey, string> = {
  gpt55: "var(--pass)",
  gpt54: "var(--codex)",
  gpt54Mini: "var(--cyan)",
  claudeOpus48: "var(--claude)",
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
    xDomain: [0, 45],
    yDomain: [0, 100],
    xTicks: [0, 15, 30, 45],
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
    yDomain: [0, 45],
    xTicks: [0, 25, 50, 75, 100],
    yTicks: [0, 15, 30, 45],
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
  const effortLabel = run.effort ? ` · ${run.effort}` : "";

  return {
    ...run,
    agentMinutes: formatMinutes(run.agentTimeSeconds),
    label: `${run.agent}${effortLabel} · ${run.passRate}%`,
    color: run.series ? seriesColors[run.series] : run.current ? "var(--pass)" : `var(--${run.kind})`,
  };
}

function buildSeries(chartData: ChartPoint[]) {
  const groups = new Map<ModelKey, ChartPoint[]>();
  const standaloneData: ChartPoint[] = [];

  for (const point of chartData) {
    if (!point.series) {
      standaloneData.push(point);
      continue;
    }

    const series = groups.get(point.series) ?? [];
    series.push(point);
    groups.set(point.series, series);
  }

  const linkedSeries: ChartSeries[] = [];

  for (const [key, points] of groups) {
    const sortedPoints = [...points].sort((a, b) => {
      const aOrder = a.effort ? effortOrder[a.effort] : 0;
      const bOrder = b.effort ? effortOrder[b.effort] : 0;
      return aOrder - bOrder;
    });

    if (sortedPoints.length > 1) {
      linkedSeries.push({
        key,
        label: sortedPoints[0].agent,
        color: seriesColors[key],
        points: sortedPoints,
      });
    } else {
      standaloneData.push(sortedPoints[0]);
    }
  }

  return { linkedSeries, standaloneData };
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ChartPoint }> }) {
  if (!active || !payload?.length) {
    return null;
  }

  const run = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>{run.agent}</strong>
      <span>
        {run.corpus}
        {run.effort ? ` · ${run.effort}` : ""}
      </span>
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
  const { linkedSeries, standaloneData } = useMemo(() => buildSeries(chartData), [chartData]);
  const config = chartModes[mode];

  return (
    <section className="section leaderboard-section" id="leaderboard" aria-labelledby="leaderboard-heading">
      <div className="section-heading compact">
        <h2 id="leaderboard-heading">Run plot</h2>
      </div>

      <div className="leaderboard-panel">
        <div className="control-bar" aria-label="Run plot controls">
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
              <strong>26 tasks</strong> · updated <strong>June 25, 2026</strong>
            </span>
            <button className="filter-button" type="button">
              Runs <span>({leaderboardRuns.length}/{leaderboardRuns.length})</span>
            </button>
          </div>
        </div>

        <div className="score-plot react-chart-frame" role="img" aria-label={config.label}>
          <div className="plot-header">
            <div className="plot-title">NixBench score</div>
            <span className="plot-note">pass rate by agent time</span>
          </div>
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
                {linkedSeries.map((series) => (
                  <Scatter
                    key={series.key}
                    data={series.points}
                    fill={series.color}
                    line={{ stroke: series.color, strokeWidth: 2, strokeOpacity: 0.68 }}
                    lineType="joint"
                    name={series.label}
                    stroke="var(--panel)"
                    strokeWidth={2}
                  />
                ))}
                {standaloneData.map((entry) => (
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
                <strong>{run.marker}</strong>{" "}
                {run.effort ?? run.agent.replace("Claude ", "")} · {run.passRate}%
              </span>
            ))}
          </div>
        </div>

        <div className="leaderboard-table-wrap">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th scope="col">Run</th>
                <th scope="col">Effort</th>
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
                  <td>{run.effort ?? "default"}</td>
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
