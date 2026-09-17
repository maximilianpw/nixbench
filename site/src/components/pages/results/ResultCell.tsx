import { StatusBadge } from "@/components/pages/results/StatusBadge";
import type { TaskRunCell } from "@/data/benchmark";

export type ResultCellProps = {
  cell?: TaskRunCell;
};

export function ResultCell({ cell }: ResultCellProps) {
  if (!cell) {
    return (
      <span className="flex min-w-24 items-center justify-between gap-2 opacity-60">
        <StatusBadge status="missing" />
        <span>--</span>
      </span>
    );
  }

  return (
    <span className="flex min-w-24 items-center justify-between gap-2 font-mono text-xs tabular-nums">
      <StatusBadge status={cell.status} />
      <span>{cell.seconds == null ? "..." : `${cell.seconds.toFixed(1)}s`}</span>
    </span>
  );
}
