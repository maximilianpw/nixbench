import { cn } from "@/lib/utils";

export type StatGridProps = { items: readonly (readonly [string, string])[]; label: string; className?: string };

export function StatGrid({ items, label, className }: StatGridProps) {
  return (
    <dl className={cn("divide-y border-y", className)} aria-label={label}>
      {items.map(([labelText, value]) => (
        <div className="flex items-center justify-between gap-4 py-3" key={labelText}>
          <dt className="font-mono text-xs uppercase tracking-wider text-muted-foreground">{labelText}</dt>
          <dd className="font-mono text-sm font-semibold tabular-nums">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
