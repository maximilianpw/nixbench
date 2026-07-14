import type { AgentKind, LeaderboardAggregate, ModelKey, ReasoningEffort } from "@/data/benchmark";

export type AggregateChartPoint = LeaderboardAggregate & {
  datumType: "aggregate";
  tasksPassedMean: number;
  secondsPerTaskMean: number;
  tasksPassedError: [number, number];
  secondsPerTaskError: [number, number];
  pointSize: number;
  color: string;
  label: string;
};

export type TrialChartPoint = {
  datumType: "trial";
  id: string;
  configurationId: string;
  agent: string;
  kind: AgentKind;
  corpus: string;
  runId: string;
  series?: ModelKey;
  effort?: ReasoningEffort;
  trial: number;
  taskCount: number;
  tasksPassed: number;
  secondsPerTask: number;
  pointSize: number;
  agentTimeLabel: string;
  failed: number;
  timeouts: number;
  color: string;
};

export type EvidenceDatum = AggregateChartPoint | TrialChartPoint;

export type ChartSeries = {
  key: string;
  label: string;
  color: string;
  aggregates: AggregateChartPoint[];
  trials: TrialChartPoint[];
};
