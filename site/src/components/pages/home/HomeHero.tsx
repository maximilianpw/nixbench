import { ArrowRight, ArrowUpRight, FolderGit2 } from "lucide-react";

import { StatGrid } from "@/components/benchmark/StatGrid";
import { Button } from "@/components/ui/button";
import {
  currentCorpusLabel,
  currentEvidenceSummary,
  currentLeaderboardAggregates,
  heroStats,
} from "@/data/benchmark";

export function HomeHero() {
  const leadingResult = currentLeaderboardAggregates
    .filter((aggregate) => aggregate.trialCount > 1)
    .sort(
      (left, right) => right.passedTasks.mean - left.passedTasks.mean || left.agentSecondsPerTask.mean - right.agentSecondsPerTask.mean,
    )[0];

  return (
    <section className="border-b" aria-labelledby="home-hero-title">
      <div className="content-shell grid gap-10 py-16 sm:py-20 lg:grid-cols-[minmax(0,1.45fr)_minmax(18rem,0.75fr)] lg:py-28">
        <div>
          <a className="eyebrow inline-flex items-center gap-2 no-underline hover:text-foreground" href="https://github.com/maximilianpw/nixbench">
            <FolderGit2 aria-hidden="true" />
            Open-source benchmark
            <ArrowUpRight aria-hidden="true" />
          </a>
          <h1 id="home-hero-title" className="mt-6 max-w-3xl text-5xl font-semibold leading-[0.95] tracking-[-0.055em] sm:text-6xl lg:text-7xl">Can AI agents write Nix that actually passes?</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
            NixBench measures coding agents on small repository repairs. Every answer is scored by a hidden shell
            evaluator—not by whether it merely looks plausible.
          </p>
          {leadingResult ? (
            <p className="mt-6 border-l-2 border-nix-blue pl-4">
              <span className="block font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">Top repeated-run average</span>
              <strong className="mt-1 block text-lg">{leadingResult.passedTasks.mean.toFixed(1)} of {leadingResult.taskCount} tasks</strong>
              <small className="mt-1 block text-sm text-muted-foreground">{leadingResult.agent.split(" via ")[0]} · {leadingResult.effort ?? "default"} effort · {leadingResult.trialCount} runs</small>
            </p>
          ) : null}
          <div className="mt-8 flex flex-wrap gap-3" role="group" aria-label="Benchmark actions">
            <Button asChild>
              <a href="#leaderboard">
                Compare models <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
            <Button asChild variant="secondary">
              <a href="/results.html">Explore detailed results</a>
            </Button>
          </div>
        </div>

        <aside className="self-end" aria-label="Current benchmark evidence">
          <StatGrid items={heroStats} label="Current benchmark statistics" />
          <div className="mt-5 border-t pt-5">
            <span className="eyebrow">Current evidence</span>
            <p className="mt-2 text-sm text-muted-foreground">
              {currentEvidenceSummary.models} models · {currentEvidenceSummary.configurations} configurations · {currentEvidenceSummary.trials} trials
            </p>
            <a className="mt-4 inline-flex items-center gap-2 text-sm font-semibold no-underline hover:text-nix-blue" href="#leaderboard">
              Jump to comparison <ArrowRight aria-hidden="true" />
            </a>
          </div>
        </aside>

        <p className="flex flex-wrap gap-x-5 gap-y-2 border-t pt-5 font-mono text-xs text-muted-foreground lg:col-span-2">
          <strong className="text-foreground">{currentCorpusLabel}</strong>
          <span>• One hidden evaluator per task</span>
          <span>• Uncertainty shown for repeated trials</span>
        </p>
      </div>
    </section>
  );
}
