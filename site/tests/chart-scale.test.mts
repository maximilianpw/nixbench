import assert from "node:assert/strict";
import { test } from "node:test";

import { buildTaskScale } from "../src/components/charts/leaderboard/chart-scale.ts";

const currentEvidence = [
  { passedTasks: { min: 19, ci95Low: 20.1 } },
  { passedTasks: { min: 21, ci95Low: 21.4 } },
  { passedTasks: { min: 22, ci95Low: 22.2 } },
];

test("focused task scale fills the chart with the observed evidence band", () => {
  const scale = buildTaskScale(currentEvidence, 29, "focused");

  assert.deepEqual(scale.domain, [18, 29]);
  assert.deepEqual(scale.ticks, [18, 20, 22, 24, 26, 28, 29]);
});

test("full task scale retains the zero baseline for context", () => {
  const scale = buildTaskScale(currentEvidence, 29, "full");

  assert.deepEqual(scale.domain, [0, 29]);
  assert.deepEqual(scale.ticks, [0, 5, 10, 15, 20, 25, 29]);
});
