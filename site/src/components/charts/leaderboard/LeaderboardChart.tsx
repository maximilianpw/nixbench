import type { CSSProperties } from "react";
import { CartesianGrid, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { LeaderboardChartTooltip } from "@/components/charts/leaderboard/ChartTooltip";
import type { ChartConfig as PlotConfig, ChartPoint, ChartSeries } from "@/components/charts/leaderboard/types";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";

export type LeaderboardChartProps = {
  chartData: ChartPoint[];
  config: PlotConfig;
  linkedSeries: ChartSeries[];
  standaloneData: ChartPoint[];
  showEffortSweep?: boolean;
};

export function LeaderboardChart({
  chartData,
  config,
  linkedSeries,
  standaloneData,
  showEffortSweep = false,
}: LeaderboardChartProps) {
  const chartConfig = buildLeaderboardChartConfig(linkedSeries, standaloneData);
  const passRateScale = buildPassRateScale(chartData);
  const xDomain = config.xKey === "passRate" ? passRateScale.domain : config.xDomain;
  const yDomain = config.yKey === "passRate" ? passRateScale.domain : config.yDomain;
  const xTicks = config.xKey === "passRate" ? passRateScale.ticks : config.xTicks;
  const yTicks = config.yKey === "passRate" ? passRateScale.ticks : config.yTicks;
  const legendItems = [
    ...linkedSeries.map((series) => ({
      key: series.key,
      label: series.label,
      color: series.color,
      runCount: series.points.length,
    })),
    ...standaloneData.map((run) => ({
      key: run.id,
      label: run.agent,
      color: run.color,
      runCount: 1,
    })),
  ];

  return (
    <Card
      className="chart-card score-plot react-chart-frame"
      aria-labelledby="leaderboard-chart-title"
      aria-describedby="leaderboard-chart-description"
    >
      <CardHeader>
        <CardTitle id="leaderboard-chart-title">Row comparison</CardTitle>
        <CardDescription id="leaderboard-chart-description">
          {showEffortSweep
            ? "Each color is a model; lines connect recorded effort levels. The pass-rate axis is zoomed to the visible range."
            : "One strongest observed row per model. Switch to all effort levels to inspect every row and its efficiency curve."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer className="chart-shell" config={chartConfig} initialDimension={{ width: 860, height: 330 }}>
          <ScatterChart accessibilityLayer margin={{ top: 48, right: 56, bottom: 42, left: 34 }}>
            <CartesianGrid stroke="var(--grid-line)" strokeDasharray="0" />
            <XAxis
              dataKey={config.xKey as string}
              domain={xDomain}
              tickFormatter={config.xFormatter}
              ticks={xTicks}
              type="number"
              label={{ value: config.xLabel, position: "insideBottomRight", offset: -18 }}
              stroke="var(--muted)"
              tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
            />
            <YAxis
              dataKey={config.yKey as string}
              domain={yDomain}
              tickFormatter={config.yFormatter}
              ticks={yTicks}
              type="number"
              label={{ value: config.yLabel, position: "insideTopLeft", offset: -26 }}
              stroke="var(--muted)"
              tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
            />
            <ZAxis range={[160, 220]} />
            <ChartTooltip cursor={{ stroke: "var(--border-strong)" }} content={<LeaderboardChartTooltip />} />
            {linkedSeries.map((series) => (
              <Scatter
                key={series.key}
                data={series.points}
                fill={chartColor(series.key, series.color)}
                line={{ stroke: chartColor(series.key, series.color), strokeWidth: 2, strokeOpacity: 0.68 }}
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
                fill={chartColor(entry.id, entry.color)}
                name={entry.label}
                stroke="var(--panel)"
                strokeWidth={2}
              />
            ))}
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <CardFooter>
        <div className="chart-legend" role="list" aria-label="Model legend">
          {legendItems.map((item) => (
            <span key={item.key} role="listitem">
              <i
                aria-hidden="true"
                style={{ "--swatch": chartColor(item.key, item.color) } as CSSProperties}
              />
              <strong>{item.label}</strong>
              <small>{item.runCount} {item.runCount === 1 ? "row" : "rows"}</small>
            </span>
          ))}
        </div>
      </CardFooter>
    </Card>
  );
}

function buildLeaderboardChartConfig(linkedSeries: ChartSeries[], standaloneData: ChartPoint[]) {
  return {
    ...Object.fromEntries(linkedSeries.map((series) => [series.key, { label: series.label, color: series.color }])),
    ...Object.fromEntries(standaloneData.map((entry) => [entry.id, { label: entry.label, color: entry.color }])),
  } satisfies ChartConfig;
}

function chartColor(key: string, fallback: string) {
  return `var(--color-${key}, ${fallback})`;
}

function buildPassRateScale(chartData: ChartPoint[]) {
  if (chartData.length === 0) {
    return { domain: [0, 100] as [number, number], ticks: [0, 25, 50, 75, 100] };
  }

  const passRates = chartData.map((run) => run.passRate);
  let lower = Math.max(0, Math.floor((Math.min(...passRates) - 5) / 5) * 5);
  let upper = Math.min(100, Math.ceil((Math.max(...passRates) + 5) / 5) * 5);

  while (upper - lower < 20) {
    if (lower > 0) {
      lower -= 5;
    }
    if (upper < 100) {
      upper += 5;
    }
  }

  const ticks: number[] = [];
  for (let tick = lower; tick <= upper; tick += 5) {
    ticks.push(tick);
  }

  return { domain: [lower, upper] as [number, number], ticks };
}
