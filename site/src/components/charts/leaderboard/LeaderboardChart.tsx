import type { CSSProperties } from "react";
import { CartesianGrid, ErrorBar, LabelList, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { LeaderboardChartTooltip } from "@/components/charts/leaderboard/ChartTooltip";
import type { ChartSeries } from "@/components/charts/leaderboard/types";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import type { LeaderboardAggregate, ModelKey } from "@/data/benchmark";
import { cn } from "@/lib/utils";

export type LeaderboardChartProps = {
  aggregates: LeaderboardAggregate[];
  series: ChartSeries[];
  taskCount: number;
  highlightedModel: ModelKey | null;
};

export function LeaderboardChart({
  aggregates,
  series,
  taskCount,
  highlightedModel,
}: LeaderboardChartProps) {
  const chartConfig = Object.fromEntries(
    series.map((entry) => [entry.key, { label: entry.label, color: entry.color }]),
  ) satisfies ChartConfig;
  const xScale = buildSecondsScale(aggregates);
  const yTicks = buildTaskTicks(taskCount);

  return (
    <Card
      className="chart-card evidence-plot react-chart-frame"
      aria-labelledby="leaderboard-chart-title"
      aria-describedby="leaderboard-chart-description"
    >
      <CardHeader>
        <div className="evidence-card-heading">
          <div>
            <CardTitle id="leaderboard-chart-title">Configuration means across corpus trials</CardTitle>
            <CardDescription id="leaderboard-chart-description">
              Mean tasks passed against mean agent seconds per task. Both axes start at zero; whiskers are 95%
              Student&apos;s t intervals.
            </CardDescription>
          </div>
          <div className="evidence-axis-note" aria-label="Chart axis summary">
            <span>↑ more tasks</span>
            <span>← less time</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ChartContainer className="chart-shell evidence-chart-shell" config={chartConfig} initialDimension={{ width: 860, height: 410 }}>
          <ScatterChart accessibilityLayer margin={{ top: 30, right: 42, bottom: 48, left: 26 }}>
            <CartesianGrid stroke="var(--grid-line)" strokeDasharray="3 5" />
            <XAxis
              dataKey="secondsPerTaskMean"
              domain={[0, xScale.upper]}
              tickFormatter={(value) => `${value}s`}
              ticks={xScale.ticks}
              type="number"
              label={{ value: "Mean agent seconds / task", position: "insideBottomRight", offset: -24 }}
              stroke="var(--muted)"
              tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
            />
            <YAxis
              dataKey="tasksPassedMean"
              domain={[0, taskCount]}
              tickFormatter={(value) => String(value)}
              ticks={yTicks}
              type="number"
              label={{ value: `Mean tasks passed / ${taskCount}`, position: "insideTopLeft", offset: -18 }}
              stroke="var(--muted)"
              tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
            />
            <ZAxis dataKey="pointSize" range={[24, 150]} />
            <ChartTooltip
              cursor={{ stroke: "var(--border-strong)", strokeDasharray: "3 4" }}
              content={<LeaderboardChartTooltip />}
            />

            {series.map((entry) => {
              const model = entry.aggregates[0]?.series;
              return (
                <Scatter
                  key={`${entry.key}-trials`}
                  className={cn(
                    "leaderboard-series",
                    isModelDimmed(highlightedModel, model) && "is-dimmed",
                  )}
                  data={entry.trials.map((trial) => ({
                    ...trial,
                    secondsPerTaskMean: trial.secondsPerTask,
                    tasksPassedMean: trial.tasksPassed,
                  }))}
                  fill={entry.color}
                  fillOpacity={highlightedModel === model ? 0.3 : 0.2}
                  isAnimationActive={false}
                  name={`${entry.label} trials`}
                  stroke={entry.color}
                  strokeOpacity={highlightedModel === model ? 0.52 : 0.32}
                />
              );
            })}

            {series.flatMap((entry) =>
              entry.aggregates.map((point) => {
                const isHighlighted = highlightedModel === point.series;

                return (
                  <Scatter
                    key={point.id}
                    className={cn(
                      "leaderboard-series",
                      isModelDimmed(highlightedModel, point.series) && "is-dimmed",
                    )}
                    data={[point]}
                    fill={point.trialCount > 1 ? entry.color : "var(--panel)"}
                    isAnimationActive={false}
                    name={point.label}
                    stroke={entry.color}
                    strokeWidth={isHighlighted ? 3 : point.trialCount > 1 ? 2 : 3}
                  >
                    {point.trialCount > 1 ? (
                      <>
                        <ErrorBar
                          dataKey="secondsPerTaskError"
                          direction="x"
                          stroke={entry.color}
                          strokeWidth={isHighlighted ? 2 : 1.5}
                          width={5}
                        />
                        <ErrorBar
                          dataKey="tasksPassedError"
                          direction="y"
                          stroke={entry.color}
                          strokeWidth={isHighlighted ? 2 : 1.5}
                          width={5}
                        />
                      </>
                    ) : null}
                    <LabelList
                      dataKey="marker"
                      fill="var(--muted)"
                      fontFamily="var(--mono)"
                      fontSize={10}
                      offset={9}
                      position="top"
                    />
                  </Scatter>
                );
              }),
            )}
          </ScatterChart>
        </ChartContainer>
      </CardContent>
      <CardFooter>
        <div className="evidence-footer">
          <div className="evidence-key" aria-label="Evidence mark key">
            <span><i className="mean-mark" aria-hidden="true" />Replicated mean + 95% CI</span>
            <span><i className="single-mark" aria-hidden="true" />Single observation or legacy composite; no CI</span>
            <span><i className="trial-mark" aria-hidden="true" />Individual trial</span>
            <small>Marks use each model&apos;s color and configuration code.</small>
          </div>
          <div className="chart-legend" role="list" aria-label="Model legend">
            {series.map((entry) => {
              const model = entry.aggregates[0]?.series;

              return (
                <span
                  key={entry.key}
                  role="listitem"
                  data-dimmed={isModelDimmed(highlightedModel, model) || undefined}
                >
                  <i aria-hidden="true" style={{ "--swatch": entry.color } as CSSProperties} />
                  <strong>{entry.label}</strong>
                  <small>{entry.aggregates.length} cfg · {entry.trials.length} trials</small>
                </span>
              );
            })}
          </div>
        </div>
      </CardFooter>
    </Card>
  );
}

function isModelDimmed(highlightedModel: ModelKey | null, model: ModelKey | undefined) {
  return highlightedModel !== null && highlightedModel !== model;
}

function buildSecondsScale(aggregates: LeaderboardAggregate[]) {
  const observedUpper = aggregates.reduce((maximum, aggregate) => {
    const high = Math.max(
      aggregate.agentSecondsPerTask.max,
      aggregate.agentSecondsPerTask.ci95High ?? 0,
    );
    return Math.max(maximum, high);
  }, 0);
  const upper = Math.max(60, Math.ceil(observedUpper / 30) * 30);
  const ticks: number[] = [];
  for (let tick = 0; tick <= upper; tick += 30) {
    ticks.push(tick);
  }
  return { upper, ticks };
}

function buildTaskTicks(taskCount: number) {
  const ticks: number[] = [];
  for (let tick = 0; tick < taskCount; tick += 5) {
    if (taskCount - tick > 2) ticks.push(tick);
  }
  ticks.push(taskCount);
  return ticks;
}
