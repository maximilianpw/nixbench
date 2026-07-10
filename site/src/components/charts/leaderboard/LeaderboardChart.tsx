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
};

export function LeaderboardChart({ chartData, config, linkedSeries, standaloneData }: LeaderboardChartProps) {
  const chartConfig = buildLeaderboardChartConfig(linkedSeries, standaloneData);

  return (
    <Card className="chart-card score-plot react-chart-frame" role="img" aria-label={config.label}>
      <CardHeader>
        <CardTitle>NixBench score</CardTitle>
        <CardDescription>Pass rate by agent time, effort, and failure count.</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer className="chart-shell" config={chartConfig} initialDimension={{ width: 860, height: 330 }}>
          <ScatterChart accessibilityLayer margin={{ top: 48, right: 56, bottom: 42, left: 34 }}>
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
        <div className="chart-legend" aria-hidden="true">
          {chartData.map((run) => (
            <span key={run.id}>
              <i style={{ "--swatch": chartColor(run.series ?? run.id, run.color) } as CSSProperties} />
              <strong>{run.marker}</strong> {run.effort ?? run.agent.replace("Claude ", "")} · {run.passRate}%
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
