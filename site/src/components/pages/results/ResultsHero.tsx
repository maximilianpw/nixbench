import { StatGrid } from "@/components/benchmark/StatGrid";
import { currentTopRun, passedTasks, resultOverviewStats } from "@/data/benchmark";

export type ResultsHeroProps = {};

export function ResultsHero({}: ResultsHeroProps = {}) {
  return (
    <section className="results-hero" aria-labelledby="results-hero-title">
      <div className="results-hero-inner">
        <div className="results-title-block">
          <p className="hero-kicker">
            <span aria-hidden="true" />
            Results matrix · June 24–July 10, 2026
          </p>
          <h1 id="results-hero-title">Benchmark results</h1>
          <p className="results-statement">Twenty-nine comparison rows. Seven model families. Two corpus versions.</p>
          <p className="results-description">
            Compare pass rate, effort, elapsed agent time, task outcomes, and failure patterns. Every row remains tied
            to its corpus denominator so historical and current runs are never presented as interchangeable.
          </p>
          {currentTopRun ? (
            <p className="results-top-note">
              <span>Current-corpus leader</span>
              <strong>{currentTopRun.agent}</strong>
              <b>{[passedTasks(currentTopRun), currentTopRun.totalTasks].join("/")}</b>
            </p>
          ) : null}
        </div>
        <StatGrid items={resultOverviewStats} label="Dataset summary" className="result-stat-grid" />
      </div>
    </section>
  );
}
