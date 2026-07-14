import { StatGrid } from "@/components/benchmark/StatGrid";
import { currentEvidenceSummary, resultOverviewStats, resultsDateRangeLabel } from "@/data/benchmark";

export function ResultsHero() {
  return (
    <section className="results-hero" aria-labelledby="results-hero-title">
      <div className="results-hero-inner">
        <div className="results-title-block">
          <p className="hero-kicker">
            <span aria-hidden="true" />
            Results evidence · {resultsDateRangeLabel}
          </p>
          <h1 id="results-hero-title">Benchmark results</h1>
          <p className="results-statement">Configuration means, individual trials, and honest uncertainty.</p>
          <p className="results-description">
            Compare integer tasks solved and normalized time per task. Historical and current corpora stay separate,
            and a confidence interval appears only when repeated trials support one.
          </p>
          <p className="results-top-note">
            <span>Current-corpus coverage</span>
            <strong>{currentEvidenceSummary.configurations} configurations</strong>
            <b>{currentEvidenceSummary.trials} trials</b>
          </p>
        </div>
        <StatGrid items={resultOverviewStats} label="Dataset summary" className="result-stat-grid" />
      </div>
    </section>
  );
}
