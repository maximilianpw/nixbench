import { Badge } from "@/components/ui/badge";
import type { TaskStatus } from "@/data/benchmark";

export type StatusBadgeProps = {
  status: TaskStatus | "missing";
};

export function StatusBadge({ status }: StatusBadgeProps) {
  if (status === "missing") {
    return <Badge variant="muted">No data</Badge>;
  }

  return <Badge variant={status}>{status === "pass" ? "Pass" : "Fail"}</Badge>;
}
