import { useMemo, useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { buildEvidenceSeries } from "@/components/charts/leaderboard/chart-data";
import type { TaskScaleMode } from "@/components/charts/leaderboard/chart-scale";
import { LeaderboardChart } from "@/components/charts/leaderboard/LeaderboardChart";
import {
  LeaderboardControls,
  type CorpusFilter,
  type EvidenceView,
} from "@/components/charts/leaderboard/LeaderboardControls";
import { LeaderboardTable } from "@/components/charts/leaderboard/LeaderboardTable";
import { currentCorpusLabel, leaderboardAggregates, type ModelKey } from "@/data/benchmark";

export function LeaderboardPanel() {
  const [corpus, setCorpus] = useState<CorpusFilter>("29-task corpus");
  const [view, setView] = useState<EvidenceView>("summary");
  const [taskScaleMode, setTaskScaleMode] = useState<TaskScaleMode>("focused");
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
    const agentVersions = [...new Set(trials.map((trial) => trial.agentVersion).filter(Boolean))];
    const corpusRevisions = [...new Set(trials.map((trial) => trial.corpusRevision).filter(Boolean))];
    const hosts = [...new Set(trials.map((trial) => trial.host).filter(Boolean))];
    const networks = [...new Set(trials.map((trial) => trial.network).filter(Boolean))];
    const timeoutBudgets = [
      ...new Set(
        trials
          .map((trial) => trial.agentTimeoutSeconds)
          .filter((seconds): seconds is number => seconds != null),
      ),
    ].sort((left, right) => left - right);
    if (!agentVersions.length || !corpusRevisions.length || !hosts.length || !networks.length) return null;
    return { agentVersions, corpusRevisions, hosts, networks, timeoutBudgets };
  }, [aggregates, corpus]);

  function changeCorpus(nextCorpus: CorpusFilter) {
    setCorpus(nextCorpus);
    setHighlightedModel(null);
  }

  return (
    <PageSection id="leaderboard" className="leaderboard-section" labelledBy="leaderboard-heading">
      <SectionHeader
        title="Benchmark results"
        description="Compare pass rates, runtime, and repeated trials across models and agent configurations."
        headingId="leaderboard-heading"
        compact
      />

      <div className="leaderboard-panel">
        <LeaderboardControls
          corpus={corpus}
          onCorpusChange={changeCorpus}
          view={view}
          onViewChange={setView}
          taskScaleMode={taskScaleMode}
          onTaskScaleModeChange={setTaskScaleMode}
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
          onHighlightedModelChange={setHighlightedModel}
          view={view}
          taskScaleMode={taskScaleMode}
        />
        <LeaderboardTable
          aggregates={aggregates}
          highlightedModel={highlightedModel}
          onHighlightedModelChange={setHighlightedModel}
        />

        <details className="data-notes">
          <summary>About this data</summary>
          <div>
            <p className="source-note">
              Corpora are kept separate and runtime is normalized per task. Lines connect configurations from lower to
              higher effort; they do not imply continuous or monotonic scaling. See the{" "}
              <a href="/docs/reproducibility.html">reproducibility method</a>
              {corpus === currentCorpusLabel ? (
                <> and <a href="/docs/runs/2026-09-10-astra-pi-isolated.html">Astra/Pi run provenance</a>.
                  Raw run IDs appear in trial tooltips.</>
              ) : (
                <> and <a href="/docs/runs/2026-06-24-model-comparison.html">historical run provenance</a>.</>
              )}
            </p>
            {currentProvenance ? (
              <p className="source-note provenance-note">
                Environments: {currentProvenance.agentVersions.length} agent version(s) · {currentProvenance.hosts.length} host(s) ·{" "}
                {currentProvenance.corpusRevisions.length} repository revision(s) · {currentProvenance.networks.length} network state(s) · timeout budgets{" "}
                {currentProvenance.timeoutBudgets.length > 0 ? (
                  <code>{currentProvenance.timeoutBudgets.map((seconds) => `${seconds}s`).join(", ")}</code>
                ) : (
                  "unrecorded"
                )}.
              </p>
            ) : null}
          </div>
        </details>
      </div>
    </PageSection>
  );
}
