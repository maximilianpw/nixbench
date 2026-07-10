import { ArrowDown, ArrowRight, TerminalSquare } from "lucide-react";

import { InlineSeparator } from "@/components/benchmark/InlineSeparator";
import { StatGrid } from "@/components/benchmark/StatGrid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { currentCorpusLabel, heroStats, passedTasks, topRun } from "@/data/benchmark";

export type HomeHeroProps = {};

export function HomeHero({}: HomeHeroProps = {}) {
  return (
    <section className="product-hero">
      <div className="product-hero-inner">
        <div className="hero-copy">
          <Badge variant="codex">NixBench · {currentCorpusLabel}</Badge>
          <h1>Can coding agents write Nix that actually passes?</h1>
          <p className="hero-lede">
            Objective repository-repair tasks scored by hidden shell evaluators—not by whether the output merely looks
            plausible.
          </p>
          <div className="actions" aria-label="Page actions">
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
          <a className="inline-jump" href="#tasks">
            Inspect the task corpus <ArrowDown data-icon="inline-end" aria-hidden="true" />
          </a>
        </div>

        <div className="benchmark-specimen" aria-label="Benchmark run artifact preview">
          <div className="specimen-header">
            <span>Top recorded run</span>
            <Badge variant="pass">{topRun ? `${passedTasks(topRun)}/${topRun.totalTasks} pass` : "No runs"}</Badge>
          </div>
          {topRun ? (
            <div className="specimen-lead">
              <strong>{topRun.agent}</strong>
              <span>
                {topRun.corpus} · {topRun.effort ?? "default"} effort · {topRun.agentTimeLabel}
              </span>
            </div>
          ) : null}
          <StatGrid items={heroStats} label="Benchmark summary" className="hero-stat-grid" />
          <InlineSeparator />
          <div className="specimen-rows" aria-hidden="true">
            <span className="trace-line pass">module-system-boundaries</span>
            <span className="trace-line pass">python-cuda-uv2nix-patch</span>
            <span className="trace-line fail">debug-network-false-lead</span>
            <span className="trace-line pass">flake-per-system-outputs</span>
          </div>
        </div>
      </div>
    </section>
  );
}
