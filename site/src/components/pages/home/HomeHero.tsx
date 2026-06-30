import { ArrowDown, ArrowRight, TerminalSquare } from "lucide-react";

import { InlineSeparator } from "@/components/benchmark/InlineSeparator";
import { StatGrid } from "@/components/benchmark/StatGrid";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { heroStats } from "@/data/benchmark";

export type HomeHeroProps = {};

export function HomeHero({}: HomeHeroProps = {}) {
  return (
    <section className="product-hero">
      <div className="product-hero-inner">
        <div className="hero-copy">
          <Badge variant="codex">v0.2 benchmark corpus</Badge>
          <div className="title-row">
            <span className="title-mark" aria-hidden="true">
              λ
            </span>
            <h1>NixBench</h1>
          </div>
          <p className="byline">agentic Nix benchmark</p>
          <p className="hero-lede">
            Objective Nix repair tasks for AI coding agents, scored by hidden shell evaluators and preserved as
            diff-backed run artifacts.
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
            <span>results/20260625T073228Z-a5a4a383</span>
            <Badge variant="pass">22/26 pass</Badge>
          </div>
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
