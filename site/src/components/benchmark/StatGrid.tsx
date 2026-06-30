import { cn } from "@/lib/utils";

export type StatGridProps = {
  items: readonly (readonly [string, string])[];
  label: string;
  className?: string;
};

export function StatGrid({ items, label, className }: StatGridProps) {
  return (
    <dl className={cn("stat-grid", className)} aria-label={label}>
      {items.map(([labelText, value]) => (
        <div key={labelText}>
          <dt>{labelText}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}
