import { useMemo, useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { buildChartPoint, buildSeries, chartModes } from "@/components/charts/leaderboard/chart-data";
import { LeaderboardChart } from "@/components/charts/leaderboard/LeaderboardChart";
import { LeaderboardControls } from "@/components/charts/leaderboard/LeaderboardControls";
import { LeaderboardTable } from "@/components/charts/leaderboard/LeaderboardTable";
import type { ChartMode } from "@/components/charts/leaderboard/types";
import { leaderboardRuns } from "@/data/benchmark";

export type LeaderboardPanelProps = {};

export function LeaderboardPanel({}: LeaderboardPanelProps = {}) {
  const [mode, setMode] = useState<ChartMode>("score");
  const chartData = useMemo(() => leaderboardRuns.map(buildChartPoint), []);
  const { linkedSeries, standaloneData } = useMemo(() => buildSeries(chartData), [chartData]);
  const config = chartModes[mode];

  return (
    <PageSection id="leaderboard" className="leaderboard-section" labelledBy="leaderboard-heading">
      <SectionHeader eyebrow="Leaderboard" title="All scored runs" headingId="leaderboard-heading" compact />

      <div className="leaderboard-panel">
        <LeaderboardControls mode={mode} onModeChange={setMode} />
        <LeaderboardChart
          chartData={chartData}
          config={config}
          linkedSeries={linkedSeries}
          standaloneData={standaloneData}
        />
        <LeaderboardTable runs={leaderboardRuns} />

        <p className="source-note">
          Current rows are local artifacts from <code>results/</code>. The model comparison is summarized in{" "}
          <a href="docs/runs/2026-06-24-model-comparison.html">run notes</a>.
        </p>
      </div>
    </PageSection>
  );
}
