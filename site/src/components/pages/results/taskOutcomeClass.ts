import type { TaskRunCell } from "@/data/benchmark";

export function taskOutcomeClass(cells: (TaskRunCell | undefined)[]) {
  const completedCells = cells.filter((cell): cell is TaskRunCell => Boolean(cell));
  if (completedCells.length === 0) return "opacity-60";
  if (completedCells.every((cell) => cell.status === "pass")) return "bg-pass/5";
  if (completedCells.every((cell) => cell.status === "fail")) return "bg-fail/5";
  return "bg-amber/5";
}
