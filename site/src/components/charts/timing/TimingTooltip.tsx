export type TimingTooltipProps = {
  active?: boolean;
  payload?: Array<{ name: string; value?: number; color: string }>;
  label?: string;
};

export function TimingTooltip({ active, payload, label }: TimingTooltipProps) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <strong>{label}</strong>
      <dl>
        {payload.map((entry) => (
          <div key={entry.name}>
            <dt>{entry.name}</dt>
            <dd>{entry.value == null ? "--" : `${entry.value.toFixed(1)}s`}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
