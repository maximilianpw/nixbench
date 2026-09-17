export type TimingTooltipProps = { active?: boolean; payload?: Array<{ name: string; value?: number; color: string }>; label?: string };

export function TimingTooltip({ active, payload, label }: TimingTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="grid min-w-48 gap-2 rounded-md border bg-popover p-3 text-xs text-popover-foreground shadow-md">
      <strong>{label}</strong>
      <dl className="grid gap-1.5">
        {payload.map((entry) => (
          <div className="flex items-center justify-between gap-4" key={entry.name}>
            <dt className="text-muted-foreground">{entry.name}</dt>
            <dd className="font-mono font-semibold tabular-nums">{entry.value == null ? "--" : `${entry.value.toFixed(1)}s`}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
