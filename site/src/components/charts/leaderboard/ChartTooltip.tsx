import type { ChartPoint } from "@/components/charts/leaderboard/types";

export type ChartTooltipProps = {
  active?: boolean;
  payload?: Array<{ payload: ChartPoint }>;
};

export function LeaderboardChartTooltip({ active, payload }: ChartTooltipProps) {
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
