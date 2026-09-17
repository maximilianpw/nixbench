import { CartesianGrid, ErrorBar, LabelList, Scatter, ScatterChart, XAxis, YAxis, ZAxis } from "recharts";

import { LeaderboardChartTooltip } from "@/components/charts/leaderboard/ChartTooltip";
import {
  buildSecondsScale,
  buildTaskScale,
  type TaskScaleMode,
} from "@/components/charts/leaderboard/chart-scale";
import type { EvidenceView } from "@/components/charts/leaderboard/LeaderboardControls";
import type { ChartSeries } from "@/components/charts/leaderboard/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartContainer, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import type { LeaderboardAggregate, ModelKey } from "@/data/benchmark";

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
  const mobileSummaries = series.map((entry) => {
    const best = [...entry.aggregates].sort(
      (left, right) => right.tasksPassedMean - left.tasksPassedMean || left.secondsPerTaskMean - right.secondsPerTaskMean,
    )[0];
    return { entry, best };
  });

  return (
    <Card
      className="gap-0 overflow-hidden py-0"
      aria-labelledby="leaderboard-chart-title"
      aria-describedby="leaderboard-chart-description"
    >
      <CardHeader className="border-b py-6">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <CardTitle id="leaderboard-chart-title">Tasks solved vs. time</CardTitle>
            <CardDescription id="leaderboard-chart-description">
              Higher is better; farther left is faster. Select a model to inspect effort levels and uncertainty.
            </CardDescription>
            <details className="mt-3 text-sm text-muted-foreground">
              <summary className="cursor-pointer font-semibold text-foreground">How to read this chart</summary>
              <p className="mt-2 max-w-3xl leading-6">
                Each point is an average for one effort setting. Paths connect effort settings for the same model.
                Repeated runs receive 95% Student&apos;s t intervals. The time axis uses {xScale.scale} spacing
                {xScale.scale === "log" ? " because runtimes span more than one order of magnitude" : ""}.
                {taskScaleMode === "focused"
                  ? ` The task axis is zoomed to ${yScale.domain[0]}–${yScale.domain[1]}.`
                  : " The task axis starts at zero."}
                {view === "summary" ? " Individual runs are hidden." : " Faint points show individual runs."}
              </p>
            </details>
          </div>
          <div className="flex shrink-0 flex-wrap gap-2 lg:max-w-52" aria-label="Chart axis summary">
            <Badge variant="muted">
              {taskScaleMode === "focused" ? "Zoomed" : "Starts at zero"}: {yScale.domain[0]}–{yScale.domain[1]} tasks
            </Badge>
            <Badge variant="muted">{xScale.scale === "log" ? "Logarithmic" : "Linear"} time</Badge>
            <span className="font-mono text-xs text-muted-foreground">↑ more tasks</span>
            <span className="font-mono text-xs text-muted-foreground">← less time</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="p-5 md:hidden" aria-label="Best observed result by model">
          <p className="eyebrow mb-3">Best observed average for each visible model</p>
          <ol className="divide-y rounded-md border">
            {mobileSummaries.map(({ entry, best }) => best ? (
              <li className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1 p-3 text-sm" key={entry.key}>
                <span className="flex items-center gap-2"><i className="size-2.5 rounded-full" aria-hidden="true" style={{ backgroundColor: entry.color }} />{entry.label.split(" via ")[0]}</span>
                <strong className="font-mono tabular-nums">{best.tasksPassedMean.toFixed(1)}/{best.taskCount}</strong>
                <small className="col-span-2 text-muted-foreground">{best.secondsPerTaskMean.toFixed(1)}s/task · {best.effort ?? "default"}</small>
              </li>
            ) : null)}
          </ol>
        </div>
        <ChartContainer className="hidden h-[440px] w-full p-4 md:flex" config={chartConfig} initialDimension={{ width: 860, height: 410 }}>
          <ScatterChart accessibilityLayer margin={{ top: 30, right: 42, bottom: 48, left: 26 }}>
            <CartesianGrid stroke="var(--grid-line)" strokeDasharray="3 5" />
            <XAxis
              dataKey="secondsPerTaskMean"
              domain={xScale.domain}
              scale={xScale.scale}
              tickFormatter={(value) => `${value}s`}
              ticks={xScale.ticks}
              type="number"
              label={{ value: "Mean agent seconds / task", position: "insideBottomRight", offset: -24 }}
              stroke="var(--muted-foreground)"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12, fontFamily: "IBM Plex Mono" }}
            />
            <YAxis
              dataKey="tasksPassedMean"
              domain={yScale.domain}
              tickFormatter={(value) => String(value)}
              ticks={yScale.ticks}
              type="number"
              label={{ value: `Mean tasks passed / ${taskCount}`, position: "insideTopLeft", offset: -18 }}
              stroke="var(--muted-foreground)"
              tick={{ fill: "var(--muted-foreground)", fontSize: 12, fontFamily: "IBM Plex Mono" }}
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
                  className={isModelDimmed(highlightedModel, model) ? "opacity-25" : undefined}
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
                      className={isModelDimmed(highlightedModel, model) ? "opacity-25" : undefined}
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
                    className={isModelDimmed(highlightedModel, point.series) ? "opacity-25" : undefined}
                    data={[point]}
                    fill={point.trialCount > 1 ? entry.color : "var(--card)"}
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
                        fill="var(--foreground)"
                        fontFamily="IBM Plex Mono"
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
      <CardFooter className="border-t p-5">
        <div className="grid w-full gap-5">
          <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground [&_span]:flex [&_span]:items-center [&_span]:gap-2 [&_i]:size-2.5 [&_i]:rounded-full [&_i]:border [&_i]:border-nix-blue [&_i]:bg-nix-blue/20" aria-label="Evidence mark key">
            <span>
              <i className={highlightedModel ? "mean-mark" : "trajectory-mark"} aria-hidden="true" />
              {highlightedModel ? "Selected mean + 95% CI" : "Ordered effort path + mean"}
            </span>
            <span><i className="single-mark" aria-hidden="true" />Single observation or legacy composite; no CI</span>
            {view === "trials" ? (
              <span><i className="trial-mark" aria-hidden="true" />Individual run</span>
            ) : null}
            <small className="basis-full">
              {view === "summary"
                ? highlightedModel
                  ? "Selected model shows effort labels and uncertainty."
                  : "Select a model below to reveal effort labels and uncertainty."
                : "Marks use each model's color and configuration code."}
            </small>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4" role="list" aria-label="Model legend">
            {series.map((entry) => {
              const model = entry.aggregates[0]?.series;

              return (
                <button
                  key={entry.key}
                  role="listitem"
                  type="button"
                  aria-pressed={highlightedModel === model}
                  aria-label={highlightedModel === model ? "Show all models" : `Isolate ${entry.label}`}
                  className="grid min-h-14 grid-cols-[auto_1fr] items-center gap-x-2 rounded-md border p-3 text-left hover:bg-muted aria-pressed:border-nix-blue aria-pressed:bg-nix-blue-soft data-[dimmed=true]:opacity-40"
                  data-dimmed={isModelDimmed(highlightedModel, model) || undefined}
                  onClick={() => onHighlightedModelChange(highlightedModel === model ? null : (model ?? null))}
                >
                  <i className="row-span-2 size-2.5 rounded-full" aria-hidden="true" style={{ backgroundColor: entry.color }} />
                  <strong>{entry.label.split(" via ")[0]}</strong>
                  <small className="text-muted-foreground">
                    {entry.aggregates.length} settings · {entry.aggregates.reduce((sum, aggregate) => sum + aggregate.trialCount, 0)} runs
                  </small>
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
  default: -1,
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
