import { ArrowRight, ArrowUpRight, FolderGit2 } from "lucide-react";

import { StatGrid } from "@/components/benchmark/StatGrid";
import { Button } from "@/components/ui/button";
import { currentCorpusLabel, currentEvidenceSummary, heroStats } from "@/data/benchmark";

export function HomeHero() {
  return (
    <section className="product-hero" aria-labelledby="home-hero-title">
      <div className="product-hero-inner">
        <div className="hero-copy">
          <a className="hero-kicker" href="https://github.com/maximilianpw/nixbench">
            <FolderGit2 aria-hidden="true" />
            Open-source benchmark
            <ArrowUpRight aria-hidden="true" />
          </a>
          <h1 id="home-hero-title">Can AI agents write Nix that actually passes?</h1>
          <p className="hero-lede">
            NixBench measures coding agents on small repository repairs. Every answer is scored by a hidden shell
            evaluator—not by whether it merely looks plausible.
          </p>
          <div className="actions" role="group" aria-label="Benchmark actions">
            <Button asChild>
              <a href="/results.html">
                View results <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
            <Button asChild variant="secondary">
              <a href="https://github.com/maximilianpw/nixbench">
                View project <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
          </div>
        </div>

        <aside className="hero-evidence" aria-label="Current benchmark evidence">
          <StatGrid items={heroStats} label="Current benchmark statistics" className="hero-stat-grid" />
          <div className="hero-evidence-note">
            <span>Current evidence</span>
            <p>
              {currentEvidenceSummary.models} models · {currentEvidenceSummary.configurations} configurations · {currentEvidenceSummary.trials} trials
            </p>
            <a href="#leaderboard">
              Inspect the data <ArrowRight aria-hidden="true" />
            </a>
          </div>
        </aside>

        <p className="hero-corpus-note">
          <strong>{currentCorpusLabel}</strong>
          <span>One hidden evaluator per task</span>
          <span>Uncertainty shown for repeated trials</span>
        </p>
      </div>
    </section>
  );
}
