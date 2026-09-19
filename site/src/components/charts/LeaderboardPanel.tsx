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

export type LeaderboardPanelProps = {
  showHeading?: boolean;
  headingTitle?: string;
  headingDescription?: string;
  compact?: boolean;
};

type ModelFilter = ModelKey | "all";
type EvidenceFilter = "all" | "repeated";

export function LeaderboardPanel({
  showHeading = true,
  headingTitle = "Benchmark results",
  headingDescription = "See which configurations solve the most tasks, how long they take, and how much evidence supports each result.",
  compact = false,
}: LeaderboardPanelProps) {
  const [corpus, setCorpus] = useState<CorpusFilter>("29-task corpus");
  const [view, setView] = useState<EvidenceView>("summary");
  const [taskScaleMode, setTaskScaleMode] = useState<TaskScaleMode>("focused");
  const [modelFilter, setModelFilter] = useState<ModelFilter>("all");
  const [evidenceFilter, setEvidenceFilter] = useState<EvidenceFilter>("repeated");
  const [highlightedModel, setHighlightedModel] = useState<ModelKey | null>(null);
  const corpusAggregates = useMemo(
    () => leaderboardAggregates.filter((aggregate) => aggregate.corpus === corpus),
    [corpus],
  );
  const modelOptions = useMemo(() => {
    const options = new Map<ModelKey, string>();
    const optionAggregates = evidenceFilter === "repeated"
      ? corpusAggregates.filter((aggregate) => aggregate.trialCount > 1)
      : corpusAggregates;
    for (const aggregate of optionAggregates) {
      if (aggregate.series && !options.has(aggregate.series)) {
        options.set(aggregate.series, aggregate.agent.split(" via ")[0]);
      }
    }
    return [...options].map(([value, label]) => ({ value, label }));
  }, [corpusAggregates, evidenceFilter]);
  const aggregates = useMemo(
    () => corpusAggregates.filter((aggregate) => {
      const matchesModel = modelFilter === "all" || aggregate.series === modelFilter;
      const matchesEvidence = evidenceFilter === "all" || aggregate.trialCount > 1;
      return matchesModel && matchesEvidence;
    }),
    [corpusAggregates, evidenceFilter, modelFilter],
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
    setEvidenceFilter(nextCorpus === "26-task corpus" ? "all" : "repeated");
    setModelFilter("all");
    setHighlightedModel(null);
  }

  function changeEvidence(nextFilter: EvidenceFilter) {
    setEvidenceFilter(nextFilter);
    setModelFilter("all");
    setHighlightedModel(null);
  }

  function changeModel(value: string) {
    const nextModel = modelOptions.find((option) => option.value === value)?.value ?? "all";
    setModelFilter(nextModel);
    setHighlightedModel(null);
  }

  return (
    <PageSection id="leaderboard" labelledBy={showHeading ? "leaderboard-heading" : undefined}>
      {showHeading ? (
        <SectionHeader
          title={headingTitle}
          description={headingDescription}
          headingId="leaderboard-heading"
          compact
        />
      ) : null}

      <div className="space-y-6">
        {!compact ? <LeaderboardControls
          corpus={corpus}
          onCorpusChange={changeCorpus}
          view={view}
          onViewChange={setView}
          taskScaleMode={taskScaleMode}
          onTaskScaleModeChange={setTaskScaleMode}
          modelFilter={modelFilter}
          onModelFilterChange={changeModel}
          modelOptions={modelOptions}
          evidenceFilter={evidenceFilter}
          onEvidenceFilterChange={changeEvidence}
          modelCount={series.length}
          configurationCount={aggregates.length}
          trialCount={trialCount}
          replicatedConfigurationCount={replicatedConfigurationCount}
        /> : null}
        {aggregates.length > 0 ? (
          <>
            <LeaderboardChart
              aggregates={aggregates}
              series={series}
              taskCount={aggregates[0]?.taskCount ?? 0}
              highlightedModel={highlightedModel}
              onHighlightedModelChange={setHighlightedModel}
              view={view}
              taskScaleMode={taskScaleMode}
            />
            {!compact ? (
              <LeaderboardTable
                aggregates={aggregates}
                highlightedModel={highlightedModel}
                onHighlightedModelChange={setHighlightedModel}
              />
            ) : null}
          </>
        ) : (
          <div className="rounded-lg border border-dashed bg-card p-10 text-center" role="status">
            <strong className="text-lg">{compact ? "No repeated-run results are available yet." : "No repeated runs for this model."}</strong>
            <p className="mt-2 text-sm text-muted-foreground">{compact ? "Open the full results explorer to view every recorded run." : "Choose “All results” or select another model."}</p>
          </div>
        )}

        {compact ? (
          <p className="text-right text-sm font-semibold">
            <a className="text-nix-blue" href="/results.html">Open the full results explorer →</a>
          </p>
        ) : null}

        {!compact ? <details className="rounded-lg border bg-card p-4 text-sm">
          <summary className="cursor-pointer font-semibold">About this data</summary>
          <div className="mt-4 space-y-3 leading-6 text-muted-foreground">
            <p>
              Corpora are kept separate and runtime is normalized per task. Lines connect configurations from lower to
              higher effort; they do not imply continuous or monotonic scaling. See the{" "}
              <a href="/docs/reproducibility.html">reproducibility method</a>
              {corpus === currentCorpusLabel ? (
                <> and <a href="/docs/runs/2026-09-10-astra-pi-isolated.html">Astra/Pi run provenance</a>.
                  Raw run IDs appear in individual-run tooltips.</>
              ) : (
                <> and <a href="/docs/runs/2026-06-24-model-comparison.html">historical run provenance</a>.</>
              )}
            </p>
            {currentProvenance ? (
              <p>
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
        </details> : null}
      </div>
    </PageSection>
  );
}
