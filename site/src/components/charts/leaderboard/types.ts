import type { LeaderboardRun, ModelKey } from "@/data/benchmark";

export type ChartMode = "score" | "time" | "failures";

export type ChartPoint = LeaderboardRun & {
  agentMinutes: number;
  label: string;
  color: string;
};

export type ChartSeries = {
  key: ModelKey;
  label: string;
  color: string;
  points: ChartPoint[];
};

export type ChartConfig = {
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
};
