import { ArrowRight, TerminalSquare } from "lucide-react";

import { BrandMark } from "@/components/BrandMark";
import { StatGrid } from "@/components/benchmark/StatGrid";
import { Button } from "@/components/ui/button";
import { currentCorpusLabel, currentTopRun, heroStats, passedTasks } from "@/data/benchmark";

export type HomeHeroProps = {};

export function HomeHero({}: HomeHeroProps = {}) {
  return (
    <section className="product-hero" aria-labelledby="home-hero-title">
      <div className="product-hero-inner">
        <div className="hero-lockup">
          <div className="hero-identity">
            <BrandMark className="hero-symbol" />
            <div>
              <p className="hero-kicker">
                <span aria-hidden="true" />
                Open benchmark for agentic Nix
              </p>
              <h1 id="home-hero-title">NixBench</h1>
            </div>
          </div>
          <StatGrid items={heroStats} label="Current benchmark statistics" className="hero-stat-grid" />
        </div>

        <div className="hero-intro">
          <div className="hero-copy">
            <p className="hero-statement">Can coding agents write Nix that actually passes?</p>
            <p className="hero-lede">
              Objective repository-repair tasks scored by hidden shell evaluators—not by whether the output merely
              looks plausible.
            </p>
            <div className="actions" role="group" aria-label="Benchmark actions">
              <Button asChild>
                <a href="results.html">
                  Compare results <ArrowRight data-icon="inline-end" aria-hidden="true" />
                </a>
              </Button>
              <Button asChild variant="secondary">
                <a href="https://github.com/maximilianpw/nixbench#quick-start">
                  Run locally <TerminalSquare data-icon="inline-end" aria-hidden="true" />
                </a>
              </Button>
            </div>
          </div>

          <aside className="hero-run-note" aria-label="Current-corpus benchmark leader">
            <span>Current-corpus leader</span>
            <strong>{currentTopRun?.agent ?? "No completed runs"}</strong>
            {currentTopRun ? (
              <p>
                <b>{[passedTasks(currentTopRun), currentTopRun.totalTasks].join("/")}</b> pass · {currentTopRun.corpus} ·{" "}
                {currentTopRun.effort ?? "default"} effort
              </p>
            ) : null}
            <a href="#leaderboard">
              Explore all 29 rows <ArrowRight aria-hidden="true" />
            </a>
          </aside>
        </div>

        <p className="hero-corpus-note">
          Current release: <strong>{currentCorpusLabel}</strong> · one hidden evaluator per task · zero LLM judges
        </p>
      </div>
    </section>
  );
}
