import { StatGrid } from "@/components/benchmark/StatGrid";
import { Badge } from "@/components/ui/badge";
import { resultOverviewStats, topRun, passedTasks } from "@/data/benchmark";

export type ResultsHeroProps = {};

export function ResultsHero({}: ResultsHeroProps = {}) {
  return (
    <section className="results-hero">
      <div className="results-hero-inner">
        <div>
          <Badge variant="codex">Results matrix</Badge>
          <p className="eyebrow">June 24–July 10, 2026</p>
          <h1>Every model run in one comparison surface.</h1>
          <p>
            NixBench tracks model families, effort sweeps, task outcomes, and timing across the recorded 26- and
            29-task corpus versions.
            {topRun ? ` The leading row is ${topRun.agent} at ${passedTasks(topRun)}/${topRun.totalTasks}.` : null}
          </p>
        </div>
        <StatGrid items={resultOverviewStats} label="Dataset summary" className="result-stat-grid" />
      </div>
    </section>
  );
}
