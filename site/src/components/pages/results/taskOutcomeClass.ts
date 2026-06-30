import type { TaskRunCell } from "@/data/benchmark";

export function taskOutcomeClass(cells: (TaskRunCell | undefined)[]) {
  const completedCells = cells.filter((cell): cell is TaskRunCell => Boolean(cell));

  if (completedCells.length === 0) {
    return "outcome-missing";
  }

  if (completedCells.every((cell) => cell.status === "pass")) {
    return "outcome-mutual-pass";
  }
  if (completedCells.every((cell) => cell.status === "fail")) {
    return "outcome-mutual-fail";
  }
  return "outcome-split";
}
