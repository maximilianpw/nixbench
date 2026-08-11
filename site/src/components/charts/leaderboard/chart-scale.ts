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

export type SecondsEvidenceRange = {
  agentSecondsPerTask: {
    min: number;
    max: number;
    ci95High?: number;
  };
};

export type SecondsScale = {
  domain: [number, number];
  ticks: number[];
  scale: "linear" | "log";
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

export function buildSecondsScale(aggregates: SecondsEvidenceRange[]): SecondsScale {
  const positiveMinimum = aggregates.reduce((minimum, aggregate) => {
    const candidate = aggregate.agentSecondsPerTask.min;
    return candidate > 0 ? Math.min(minimum, candidate) : minimum;
  }, Infinity);
  const observedUpper = aggregates.reduce((maximum, aggregate) => {
    const high = Math.max(
      aggregate.agentSecondsPerTask.max,
      aggregate.agentSecondsPerTask.ci95High ?? 0,
    );
    return Math.max(maximum, high);
  }, 0);

  if (Number.isFinite(positiveMinimum) && observedUpper / positiveMinimum >= 12) {
    const ticks = buildLogTicks(positiveMinimum, observedUpper);
    return {
      domain: [ticks[0], ticks[ticks.length - 1]],
      ticks,
      scale: "log",
    };
  }

  const upper = Math.max(60, Math.ceil(observedUpper / 30) * 30);
  const ticks: number[] = [];
  for (let tick = 0; tick <= upper; tick += 30) ticks.push(tick);
  return { domain: [0, upper], ticks, scale: "linear" };
}

function buildLogTicks(lower: number, upper: number) {
  const ticks: number[] = [];
  let exponent = Math.floor(Math.log10(lower));
  while (ticks.length === 0 || ticks[ticks.length - 1] < upper) {
    const magnitude = 10 ** exponent;
    for (const multiplier of [1, 3]) {
      const tick = multiplier * magnitude;
      if (ticks.length === 0 || tick > ticks[ticks.length - 1]) ticks.push(tick);
      if (tick >= upper) return ticks;
    }
    exponent += 1;
  }
  return ticks;
}

function buildTaskTicks(lower: number, upper: number, step: number) {
  const ticks: number[] = [];
  for (let tick = lower; tick < upper; tick += step) {
    ticks.push(tick);
  }
  ticks.push(upper);
  return ticks;
}
