import { StatusBadge } from "@/components/pages/results/StatusBadge";
import type { TaskRunCell } from "@/data/benchmark";

export type ResultCellProps = {
  cell?: TaskRunCell;
};

export function ResultCell({ cell }: ResultCellProps) {
  if (!cell) {
    return (
      <span className="result-cell missing">
        <StatusBadge status="missing" />
        <span>--</span>
      </span>
    );
  }

  return (
    <span className="result-cell">
      <StatusBadge status={cell.status} />
      <span>{cell.seconds == null ? "..." : `${cell.seconds.toFixed(1)}s`}</span>
    </span>
  );
}
