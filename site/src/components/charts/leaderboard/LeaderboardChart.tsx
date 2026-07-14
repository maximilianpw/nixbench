import type { CSSProperties } from "react";
import { CartesianGrid, ErrorBar, LabelList, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { LeaderboardChartTooltip } from "@/components/charts/leaderboard/ChartTooltip";
import {
  buildTaskScale,
  type TaskScaleMode,
} from "@/components/charts/leaderboard/chart-scale";
import type { EvidenceView } from "@/components/charts/leaderboard/LeaderboardControls";
import type { ChartSeries } from "@/components/charts/leaderboard/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import type { LeaderboardAggregate, ModelKey } from "@/data/benchmark";
import { cn } from "@/lib/utils";

export type LeaderboardChartProps = {
  aggregates: LeaderboardAggregate[];
  series: ChartSeries[];
  taskCount: number;
  highlightedModel: ModelKey | null;
  onHighlightedModelChange: (model: ModelKey | null) => void;
  view: EvidenceView;
  taskScaleMode: TaskScaleMode;
};

export function LeaderboardChart({
  aggregates,
  series,
  taskCount,
  highlightedModel,
  onHighlightedModelChange,
  view,
  taskScaleMode,
}: LeaderboardChartProps) {
  const chartConfig = Object.fromEntries(
    series.map((entry) => [entry.key, { label: entry.label, color: entry.color }]),
  ) satisfies ChartConfig;
  const xScale = buildSecondsScale(aggregates);
  const yScale = buildTaskScale(aggregates, taskCount, taskScaleMode);

  return (
    <Card
      className="chart-card evidence-plot react-chart-frame"
      aria-labelledby="leaderboard-chart-title"
      aria-describedby="leaderboard-chart-description"
    >
      <CardHeader>
        <div className="evidence-card-heading">
          <div>
            <CardTitle id="leaderboard-chart-title">Configuration means, with uncertainty</CardTitle>
            <CardDescription id="leaderboard-chart-description">
              Mean tasks passed against mean agent seconds per task. Paths connect ordered effort configurations;
              select a model to reveal its 95% Student&apos;s t intervals and effort labels.{" "}
              {taskScaleMode === "focused"
                ? `The task axis focuses on ${yScale.domain[0]}–${yScale.domain[1]} to make the observed differences legible.`
                : "The task axis shows the full zero-based context."}{" "}
              {view === "summary"
                ? "Individual trials are hidden in this summary view."
                : "Faint points are individual trials."}
            </CardDescription>
          </div>
          <div className="evidence-axis-note" aria-label="Chart axis summary">
            <Badge variant="muted">
              {taskScaleMode === "focused" ? "Focused" : "Full"}: {yScale.domain[0]}–{yScale.domain[1]} tasks
            </Badge>
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
              domain={yScale.domain}
              tickFormatter={(value) => String(value)}
              ticks={yScale.ticks}
              type="number"
              label={{ value: `Mean tasks passed / ${taskCount}`, position: "insideTopLeft", offset: -18 }}
              stroke="var(--muted)"
              tick={{ fill: "var(--muted)", fontSize: 12, fontFamily: "var(--mono)" }}
            />
            <ZAxis dataKey="pointSize" range={[14, 72]} />
            <ChartTooltip
              cursor={{ stroke: "var(--border-strong)", strokeDasharray: "3 4" }}
              content={<LeaderboardChartTooltip />}
            />

            {series.map((entry) => {
              const model = entry.aggregates[0]?.series;
              const isHighlighted = highlightedModel === model;

              return (
                <Scatter
                  key={`${entry.key}-trajectory`}
                  className={cn(
                    "effort-trajectory",
                    isModelDimmed(highlightedModel, model) && "is-dimmed",
                    isHighlighted && "is-highlighted",
                  )}
                  data={orderByEffort(entry.aggregates)}
                  fill={entry.color}
                  isAnimationActive={false}
                  legendType="none"
                  line={{
                    stroke: entry.color,
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeOpacity: isHighlighted ? 0.9 : highlightedModel === null ? 0.42 : 0.12,
                    strokeWidth: isHighlighted ? 2 : 1.25,
                  }}
                  lineJointType="linear"
                  lineType="joint"
                  name={`${entry.label} ordered effort path`}
                  shape={<HiddenTrajectoryPoint />}
                  tooltipType="none"
                />
              );
            })}

            {view === "trials"
              ? series.map((entry) => {
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
                })
              : null}

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
                    fillOpacity={isHighlighted || highlightedModel === null ? 0.88 : 0.24}
                    isAnimationActive={false}
                    name={point.label}
                    stroke={entry.color}
                    strokeOpacity={isHighlighted || highlightedModel === null ? 0.9 : 0.28}
                    strokeWidth={isHighlighted ? 2 : point.trialCount > 1 ? 1.25 : 1.75}
                  >
                    {point.trialCount > 1 && isHighlighted ? (
                      <>
                        <ErrorBar
                          dataKey="secondsPerTaskError"
                          direction="x"
                          stroke={`color-mix(in srgb, ${entry.color} ${isHighlighted ? 82 : 38}%, transparent)`}
                          strokeWidth={isHighlighted ? 1.5 : 1}
                          width={3}
                        />
                        <ErrorBar
                          dataKey="tasksPassedError"
                          direction="y"
                          stroke={`color-mix(in srgb, ${entry.color} ${isHighlighted ? 82 : 38}%, transparent)`}
                          strokeWidth={isHighlighted ? 1.5 : 1}
                          width={3}
                        />
                      </>
                    ) : null}
                    {isHighlighted ? (
                      <LabelList
                        dataKey="effort"
                        fill="var(--ink)"
                        fontFamily="var(--mono)"
                        fontSize={10}
                        offset={9}
                        position="top"
                      />
                    ) : null}
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
            <span>
              <i className={highlightedModel ? "mean-mark" : "trajectory-mark"} aria-hidden="true" />
              {highlightedModel ? "Selected mean + 95% CI" : "Ordered effort path + mean"}
            </span>
            <span><i className="single-mark" aria-hidden="true" />Single observation or legacy composite; no CI</span>
            {view === "trials" ? (
              <span><i className="trial-mark" aria-hidden="true" />Individual trial</span>
            ) : null}
            <small>
              {view === "summary"
                ? highlightedModel
                  ? "Selected model shows effort labels and uncertainty."
                  : "Select a model below to reveal effort labels and uncertainty."
                : "Marks use each model's color and configuration code."}
            </small>
          </div>
          <div className="chart-legend" role="list" aria-label="Model legend">
            {series.map((entry) => {
              const model = entry.aggregates[0]?.series;

              return (
                <button
                  key={entry.key}
                  role="listitem"
                  type="button"
                  aria-pressed={highlightedModel === model}
                  aria-label={highlightedModel === model ? "Show all models" : `Isolate ${entry.label}`}
                  data-dimmed={isModelDimmed(highlightedModel, model) || undefined}
                  onClick={() => onHighlightedModelChange(highlightedModel === model ? null : (model ?? null))}
                >
                  <i aria-hidden="true" style={{ "--swatch": entry.color } as CSSProperties} />
                  <strong>{entry.label}</strong>
                  <small>{entry.aggregates.length} cfg · {entry.trials.length} trials</small>
                </button>
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

function HiddenTrajectoryPoint() {
  return <g aria-hidden="true" />;
}

const effortOrder: Record<string, number> = {
  low: 0,
  medium: 1,
  high: 2,
  xhigh: 3,
  max: 4,
};

function orderByEffort(points: ChartSeries["aggregates"]) {
  return [...points].sort(
    (left, right) => (effortOrder[left.effort ?? ""] ?? 99) - (effortOrder[right.effort ?? ""] ?? 99),
  );
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
