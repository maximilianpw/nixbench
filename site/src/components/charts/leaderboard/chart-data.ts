import { modelColors } from "@/components/charts/model-colors";
import type { AggregateChartPoint, ChartSeries, TrialChartPoint } from "@/components/charts/leaderboard/types";
import { passedTasks, type LeaderboardAggregate, type ModelKey } from "@/data/benchmark";

export const seriesColors: Record<ModelKey, string> = modelColors;

export function buildEvidenceSeries(aggregates: LeaderboardAggregate[]): ChartSeries[] {
  const groups = new Map<string, LeaderboardAggregate[]>();

  for (const aggregate of aggregates) {
    const key = aggregate.series ?? aggregate.id;
    const group = groups.get(key) ?? [];
    group.push(aggregate);
    groups.set(key, group);
  }

  return [...groups.entries()].map(([key, entries]) => {
    const color = entries[0].series ? seriesColors[entries[0].series] : `var(--${entries[0].kind})`;
    return {
      key,
      label: entries[0].agent,
      color,
      aggregates: entries.map((entry) => buildAggregatePoint(entry, color)),
      trials: entries.flatMap((entry) => buildTrialPoints(entry, color)),
    };
  });
}

function buildAggregatePoint(aggregate: LeaderboardAggregate, color: string): AggregateChartPoint {
  return {
    ...aggregate,
    datumType: "aggregate",
    tasksPassedMean: aggregate.passedTasks.mean,
    secondsPerTaskMean: aggregate.agentSecondsPerTask.mean,
    tasksPassedError: intervalError(
      aggregate.passedTasks.mean,
      aggregate.passedTasks.ci95Low,
      aggregate.passedTasks.ci95High,
    ),
    secondsPerTaskError: intervalError(
      aggregate.agentSecondsPerTask.mean,
      aggregate.agentSecondsPerTask.ci95Low,
      aggregate.agentSecondsPerTask.ci95High,
    ),
    pointSize: 72,
    color,
    label: `${aggregate.agent} · ${aggregate.effort ?? "default"} · n=${aggregate.trialCount}`,
  };
}

function buildTrialPoints(aggregate: LeaderboardAggregate, color: string): TrialChartPoint[] {
  if (aggregate.trialCount <= 1) {
    return [];
  }

  return aggregate.trials
    .filter((run) => run.provenance !== "composite" && !run.runId.includes("(+2)"))
    .map((run, index) => ({
    datumType: "trial",
    id: run.id,
    configurationId: aggregate.id,
    agent: run.agent,
    kind: run.kind,
    corpus: run.corpus,
    runId: run.runId,
    series: run.series,
    effort: run.effort,
    trial: run.trial ?? index + 1,
    taskCount: run.totalTasks,
    tasksPassed: passedTasks(run),
    secondsPerTask: run.agentTimeSeconds / run.totalTasks,
    pointSize: 14,
    agentTimeLabel: run.agentTimeLabel,
    failed: run.failed,
    timeouts: run.timeouts,
    color,
    }));
}

function intervalError(mean: number, low?: number, high?: number): [number, number] {
  if (low == null || high == null) {
    return [0, 0];
  }
  return [mean - low, high - mean];
}
