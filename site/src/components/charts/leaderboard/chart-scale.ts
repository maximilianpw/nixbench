export type TaskScaleMode = "focused" | "full";

export type TaskEvidenceRange = {
  passedTasks: {
    min: number;
    ci95Low?: number;
  };
};

export type TaskScale = {
  domain: [number, number];
  ticks: number[];
};

export function buildTaskScale(
  aggregates: TaskEvidenceRange[],
  taskCount: number,
  mode: TaskScaleMode,
): TaskScale {
  if (mode === "focused" && aggregates.length > 0 && taskCount > 0) {
    const observedFloor = aggregates.reduce((lowest, aggregate) => {
      const intervalFloor = aggregate.passedTasks.ci95Low ?? aggregate.passedTasks.min;
      return Math.min(lowest, aggregate.passedTasks.min, intervalFloor);
    }, taskCount);
    const paddedFloor = Math.max(0, Math.floor(observedFloor) - 1);
    const lower = Math.min(paddedFloor, Math.max(0, taskCount - 6));
    const span = taskCount - lower;
    const step = span >= 8 ? 2 : 1;

    return {
      domain: [lower, taskCount],
      ticks: buildTaskTicks(lower, taskCount, step),
    };
  }

  return {
    domain: [0, taskCount],
    ticks: buildTaskTicks(0, taskCount, 5),
  };
}

function buildTaskTicks(lower: number, upper: number, step: number) {
  const ticks: number[] = [];
  for (let tick = lower; tick < upper; tick += step) {
    ticks.push(tick);
  }
  ticks.push(upper);
  return ticks;
}
