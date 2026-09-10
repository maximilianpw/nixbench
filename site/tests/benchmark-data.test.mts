import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

const trialRows = JSON.parse(
  await readFile(new URL("../src/data/benchmark-trials.json", import.meta.url), "utf8"),
) as Array<Record<string, unknown>>;

const expectedLocalRuns = {
  bonsai27Local: {
    runId: "20260809T111308Z-25eea85d",
    score: 700,
    failed: 22,
    timeouts: 4,
  },
  gemma4Local: {
    runId: "20260808T200851Z-8bab6819",
    score: 1000,
    failed: 19,
    timeouts: 3,
  },
} as const;

test("includes the local OpenCode benchmark trials", () => {
  for (const [series, expected] of Object.entries(expectedLocalRuns)) {
    const rows = trialRows.filter((row) => row.series === series);

    assert.equal(rows.length, 1, `${series} should have one recorded trial`);
    assert.equal(rows[0].kind, "opencode");
    assert.equal(rows[0].effort, "default");
    assert.equal(rows[0].runId, expected.runId);
    assert.equal(rows[0].score, expected.score);
    assert.equal(rows[0].maxScore, 2900);
    assert.equal(rows[0].failed, expected.failed);
    assert.equal(rows[0].timeouts, expected.timeouts);
    assert.equal(rows[0].completedTasks, 29);
    assert.equal(rows[0].provenance, "trial");
  }
});

test("records only the three complete isolated Astra Pi trials", () => {
  const rows = trialRows.filter((row) => row.series === "gpt6AstraPi");
  assert.equal(rows.length, 3);

  for (const [effort, score, seconds] of [
    ["low", 2200, 861.183],
    ["medium", 2300, 894.588],
    ["high", 2200, 1067.777],
  ]) {
    const row = rows.find((candidate) => candidate.effort === effort);
    assert.ok(row, `${effort} should have a recorded trial`);
    assert.equal(row.kind, "pi");
    assert.equal(row.model, "gpt-6-astra");
    assert.equal(row.score, score);
    assert.equal(row.maxScore, 2900);
    assert.equal(row.agentTimeSeconds, seconds);
    assert.equal(row.agentTimeoutSeconds, 240);
    assert.equal(row.completedTasks, 29);
    assert.equal(row.timeouts, 0);
    assert.equal(row.provenance, "trial");
  }

  assert.ok(!trialRows.some((row) => row.runId === "20260910T090054Z-09486029"),
    "extra-high router failures must not become a complete leaderboard trial");
});

test("benchmark trial IDs and run IDs remain unique", () => {
  const ids = trialRows.map((row) => row.id);
  const runIds = trialRows.map((row) => row.runId);

  assert.equal(new Set(ids).size, ids.length);
  assert.equal(new Set(runIds).size, runIds.length);
});
