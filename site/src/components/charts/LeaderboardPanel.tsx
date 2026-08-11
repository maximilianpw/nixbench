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
        title="Compare the signal first. Inspect the scatter second."
        description="Ordered effort paths lead the view. Select a model for uncertainty and effort labels, or reveal every trial to inspect the underlying variation."
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

        <p className="source-note">
          Corpora are intentionally separated and time is normalized per task. The focused y-axis is explicitly labelled;
          Full scale restores the zero baseline. Lines show configuration order from lower to higher effort; they do not
          imply continuous scaling or monotonic treatment.
          See the{" "}
          <a href="/docs/reproducibility.html">reproducibility method</a>
          {corpus === currentCorpusLabel ? (
            <> and <a href="/docs/runs/2026-08-08-local-opencode-models.html">local OpenCode run provenance</a>. Raw run IDs are shown in trial tooltips.</>
          ) : (
            <> and <a href="/docs/runs/2026-06-24-model-comparison.html">historical run provenance</a>.</>
          )}
        </p>
        {currentProvenance ? (
          <p className="source-note provenance-note">
            Current trial environments:{" "}
            {currentProvenance.agentVersions.length === 1 ? (
              <code>{currentProvenance.agentVersions[0]}</code>
            ) : (
              `${currentProvenance.agentVersions.length} agent versions`
            )}{" "}
            · {currentProvenance.hosts.length === 1 ? (
              <>host <code>{currentProvenance.hosts[0]}</code></>
            ) : (
              `${currentProvenance.hosts.length} hosts`
            )}{" "}
            · {currentProvenance.corpusRevisions.length === 1 ? (
              <>corpus <code>{currentProvenance.corpusRevisions[0]?.slice(0, 12)}</code></>
            ) : (
              `${currentProvenance.corpusRevisions.length} repository revisions`
            )}{" "}
            · {currentProvenance.networks.length === 1 ? (
              <>network <code>{currentProvenance.networks[0]}</code></>
            ) : (
              `${currentProvenance.networks.length} network states`
            )}{" "}
            · timeout budgets{" "}
            {currentProvenance.timeoutBudgets.length > 0 ? (
              <code>{currentProvenance.timeoutBudgets.map((seconds) => `${seconds}s`).join(", ")}</code>
            ) : (
              "unrecorded"
            )}.
          </p>
        ) : null}
      </div>
    </PageSection>
  );
}
