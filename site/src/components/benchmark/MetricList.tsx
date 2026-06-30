export type MetricListProps = {
  metrics: readonly (readonly [string, string])[];
};

export function MetricList({ metrics }: MetricListProps) {
  return (
    <dl className="metric-list">
      {metrics.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
