import { modelColors } from "@/components/charts/model-colors";
import { formatMinutes, type LeaderboardRun, type ModelKey } from "@/data/benchmark";
import type { ChartConfig, ChartMode, ChartPoint, ChartSeries } from "@/components/charts/leaderboard/types";

const effortOrder = {
  low: 0,
  medium: 1,
  high: 2,
  xhigh: 3,
} as const;

export const seriesColors: Record<ModelKey, string> = modelColors;

export const chartModes: Record<ChartMode, ChartConfig> = {
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

export function buildChartPoint(run: LeaderboardRun): ChartPoint {
  const effortLabel = run.effort ? ` · ${run.effort}` : "";

  return {
    ...run,
    agentMinutes: formatMinutes(run.agentTimeSeconds),
    label: `${run.agent}${effortLabel} · ${run.passRate}%`,
    color: run.series ? seriesColors[run.series] : run.current ? "var(--pass)" : `var(--${run.kind})`,
  };
}

export function buildSeries(chartData: ChartPoint[]) {
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
