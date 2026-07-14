import { useMemo, useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { buildEvidenceSeries } from "@/components/charts/leaderboard/chart-data";
import { LeaderboardChart } from "@/components/charts/leaderboard/LeaderboardChart";
import {
  LeaderboardControls,
  type CorpusFilter,
} from "@/components/charts/leaderboard/LeaderboardControls";
import { LeaderboardTable } from "@/components/charts/leaderboard/LeaderboardTable";
import { currentCorpusLabel, leaderboardAggregates, type ModelKey } from "@/data/benchmark";

export function LeaderboardPanel() {
  const [corpus, setCorpus] = useState<CorpusFilter>("29-task corpus");
  const [highlightedModel, setHighlightedModel] = useState<ModelKey | null>(null);
  const aggregates = useMemo(
    () => leaderboardAggregates.filter((aggregate) => aggregate.corpus === corpus),
    [corpus],
  );
  const series = useMemo(() => buildEvidenceSeries(aggregates), [aggregates]);
  const trialCount = aggregates.reduce((sum, aggregate) => sum + aggregate.trialCount, 0);
  const replicatedConfigurationCount = aggregates.filter((aggregate) => aggregate.trialCount > 1).length;
  const currentProvenance = useMemo(() => {
    if (corpus !== currentCorpusLabel) return null;
    const trials = aggregates.flatMap((aggregate) => aggregate.trials);
    const first = trials[0];
    if (!first?.agentVersion || !first.corpusRevision || !first.host || !first.network) return null;
    return {
      agentVersion: first.agentVersion,
      corpusRevision: first.corpusRevision,
      host: first.host,
      network: first.network,
    };
  }, [aggregates, corpus]);

  function changeCorpus(nextCorpus: CorpusFilter) {
    setCorpus(nextCorpus);
    setHighlightedModel(null);
  }

  return (
    <PageSection id="leaderboard" className="leaderboard-section" labelledBy="leaderboard-heading">
      <SectionHeader
        eyebrow="Benchmark evidence"
        title="Outcomes with their uncertainty attached."
        description="Large points are configuration means; faint points are individual corpus trials. Confidence bars appear only when repeated trials make an estimate possible."
        headingId="leaderboard-heading"
        compact
      />

      <div className="leaderboard-panel">
        <LeaderboardControls
          corpus={corpus}
          onCorpusChange={changeCorpus}
          modelCount={series.length}
          configurationCount={aggregates.length}
          trialCount={trialCount}
          replicatedConfigurationCount={replicatedConfigurationCount}
        />
        <LeaderboardChart
          aggregates={aggregates}
          series={series}
          taskCount={aggregates[0]?.taskCount ?? 0}
          highlightedModel={highlightedModel}
        />
        <LeaderboardTable
          aggregates={aggregates}
          highlightedModel={highlightedModel}
          onHighlightedModelChange={setHighlightedModel}
        />

        <p className="source-note">
          Corpora are intentionally separated. Time is normalized per task, axes begin at zero, and no line implies that
          higher effort is a continuous or monotonic treatment. See the{" "}
          <a href="/docs/reproducibility.html">reproducibility method</a>
          {corpus === currentCorpusLabel ? ". Raw run IDs are shown in trial tooltips." : (
            <> and <a href="/docs/runs/2026-06-24-model-comparison.html">historical run provenance</a>.</>
          )}
        </p>
        {currentProvenance ? (
          <p className="source-note provenance-note">
            Current trial environment: <code>{currentProvenance.agentVersion}</code> · host{" "}
            <code>{currentProvenance.host}</code> · corpus <code>{currentProvenance.corpusRevision.slice(0, 12)}</code> ·
            network <code>{currentProvenance.network}</code>.
          </p>
        ) : null}
      </div>
    </PageSection>
  );
}
