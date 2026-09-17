import type { EvidenceDatum } from "@/components/charts/leaderboard/types";
import { formatDuration } from "@/data/benchmark";

export type ChartTooltipProps = { active?: boolean; payload?: Array<{ payload: EvidenceDatum }> };
const shell = "grid min-w-64 max-w-80 gap-2 rounded-md border bg-popover p-3 text-xs text-popover-foreground shadow-md";
const eyebrow = "font-mono text-[0.68rem] font-semibold uppercase tracking-wider text-muted-foreground";

export function LeaderboardChartTooltip({ active, payload }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const datum = payload[0].payload;
  if (datum.datumType === "trial") {
    return <div className={shell}><span className={eyebrow}>Individual trial {datum.trial}</span><strong>{datum.agent}</strong><span className="text-muted-foreground">{datum.corpus} · {datum.effort ?? "default"}</span><dl className="grid gap-1"><TooltipRow label="Tasks passed" value={`${datum.tasksPassed}/${datum.taskCount}`} /><TooltipRow label="Seconds / task" value={`${datum.secondsPerTask.toFixed(1)}s`} /><TooltipRow label="Corpus time" value={datum.agentTimeLabel} /><TooltipRow label="Per-task timeout" value={formatTimeoutBudget(datum.agentTimeoutSeconds)} /><TooltipRow label="Timeouts" value={String(datum.timeouts)} /></dl><code>{datum.runId}</code></div>;
  }
  return <div className={shell}><span className={eyebrow}>{datum.provenance === "composite" ? "Legacy documented composite" : `Configuration mean · n=${datum.trialCount}`}</span><strong>{datum.agent}</strong><span className="text-muted-foreground">{datum.corpus} · {datum.effort ?? "default"}</span><dl className="grid gap-1"><TooltipRow label="Mean tasks" value={`${datum.passedTasks.mean.toFixed(1)}/${datum.taskCount}`} /><TooltipRow label="95% CI" value={formatInterval(datum.passedTasks.ci95Low, datum.passedTasks.ci95High)} /><TooltipRow label="Observed" value={`${datum.passedTasks.min.toFixed(0)}–${datum.passedTasks.max.toFixed(0)} tasks`} /><TooltipRow label="Seconds / task" value={`${datum.agentSecondsPerTask.mean.toFixed(1)}s`} /><TooltipRow label="Mean corpus time" value={formatDuration(datum.agentTimeSeconds.mean)} /><TooltipRow label="Per-task timeout" value={formatTimeoutBudget(datum.agentTimeoutSeconds)} /><TooltipRow label="Timeouts" value={String(datum.totalTimeouts)} /></dl>{datum.provenance === "composite" ? <small className="text-muted-foreground">This historical row combines one 24-task run with two supplemental task artifacts; it is not a repeated trial.</small> : datum.trialCount === 1 ? <small className="text-muted-foreground">Confidence interval unavailable from one trial.</small> : null}</div>;
}

function TooltipRow({ label, value }: { label: string; value: string }) { return <div className="flex justify-between gap-4"><dt className="text-muted-foreground">{label}</dt><dd className="font-mono font-semibold tabular-nums">{value}</dd></div>; }
function formatTimeoutBudget(seconds?: number) { return seconds == null ? "Unrecorded" : formatDuration(seconds); }
function formatInterval(low?: number, high?: number) { return low == null || high == null ? "Unavailable" : `${low.toFixed(1)}–${high.toFixed(1)}`; }
