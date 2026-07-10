import { useMemo, useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { buildChartPoint, buildSeries, chartModes } from "@/components/charts/leaderboard/chart-data";
import { LeaderboardChart } from "@/components/charts/leaderboard/LeaderboardChart";
import {
  LeaderboardControls,
  type CorpusFilter,
} from "@/components/charts/leaderboard/LeaderboardControls";
import { LeaderboardTable } from "@/components/charts/leaderboard/LeaderboardTable";
import type { ChartMode } from "@/components/charts/leaderboard/types";
import { leaderboardRuns } from "@/data/benchmark";

export type LeaderboardPanelProps = {};

export function LeaderboardPanel({}: LeaderboardPanelProps = {}) {
  const [mode, setMode] = useState<ChartMode>("score");
  const [corpus, setCorpus] = useState<CorpusFilter>("29-task corpus");
  const filteredRuns = useMemo(
    () => (corpus === "all" ? leaderboardRuns : leaderboardRuns.filter((run) => run.corpus === corpus)),
    [corpus],
  );
  const chartData = useMemo(() => filteredRuns.map(buildChartPoint), [filteredRuns]);
  const { linkedSeries, standaloneData } = useMemo(() => buildSeries(chartData), [chartData]);
  const config = chartModes[mode];
  const modelCount = new Set(filteredRuns.map((run) => run.series).filter(Boolean)).size;
  const taskLabel = corpus === "all" ? "26 & 29 tasks" : `${filteredRuns[0]?.totalTasks ?? 0} tasks`;

  return (
    <PageSection id="leaderboard" className="leaderboard-section" labelledBy="leaderboard-heading">
      <SectionHeader eyebrow="Leaderboard" title="Recorded runs" headingId="leaderboard-heading" compact />

      <div className="leaderboard-panel">
        <LeaderboardControls
          mode={mode}
          onModeChange={setMode}
          corpus={corpus}
          onCorpusChange={setCorpus}
          modelCount={modelCount}
          taskLabel={taskLabel}
          visibleRunCount={filteredRuns.length}
          totalRunCount={leaderboardRuns.length}
        />
        <LeaderboardChart
          chartData={chartData}
          config={config}
          linkedSeries={linkedSeries}
          standaloneData={standaloneData}
        />
        <LeaderboardTable runs={filteredRuns} />

        <p className="source-note">
          Each row is one recorded run from <code>results/</code>. Corpus labels remain attached because 26- and
          29-task scores use different denominators. See the{" "}
          <a href="docs/runs/2026-06-24-model-comparison.html">run notes</a>.
        </p>
      </div>
    </PageSection>
  );
}
