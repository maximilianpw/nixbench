import assert from "node:assert/strict";
import { test } from "node:test";

import { buildSecondsScale, buildTaskScale } from "../src/components/charts/leaderboard/chart-scale.ts";

const currentEvidence = [
  { passedTasks: { min: 7 } },
  { passedTasks: { min: 19, ci95Low: 20.1 } },
  { passedTasks: { min: 21, ci95Low: 21.4 } },
  { passedTasks: { min: 22, ci95Low: 22.2 } },
];

test("focused task scale fills the chart with the observed evidence band", () => {
  const scale = buildTaskScale(currentEvidence, 29, "focused");

  assert.deepEqual(scale.domain, [6, 29]);
  assert.deepEqual(scale.ticks, [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 29]);
});

test("full task scale retains the zero baseline for context", () => {
  const scale = buildTaskScale(currentEvidence, 29, "full");

  assert.deepEqual(scale.domain, [0, 29]);
  assert.deepEqual(scale.ticks, [0, 5, 10, 15, 20, 25, 29]);
});

test("seconds scale switches to sparse logarithmic ticks for local-runtime outliers", () => {
  const scale = buildSecondsScale([
    { agentSecondsPerTask: { min: 25, max: 80 } },
    { agentSecondsPerTask: { min: 1869, max: 2479 } },
  ]);

  assert.equal(scale.scale, "log");
  assert.deepEqual(scale.domain, [10, 3000]);
  assert.deepEqual(scale.ticks, [10, 30, 100, 300, 1000, 3000]);
});

test("seconds scale keeps a zero-based linear axis for a compact range", () => {
  const scale = buildSecondsScale([
    { agentSecondsPerTask: { min: 25, max: 80 } },
  ]);

  assert.equal(scale.scale, "linear");
  assert.deepEqual(scale.domain, [0, 90]);
  assert.deepEqual(scale.ticks, [0, 30, 60, 90]);
});
