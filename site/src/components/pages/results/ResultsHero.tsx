import { DownloadIcon, ExternalLinkIcon } from "lucide-react";

import { StatGrid } from "@/components/benchmark/StatGrid";
import { Button } from "@/components/ui/button";
import { currentEvidenceSummary, resultOverviewStats } from "@/data/benchmark";

export function ResultsHero() {
  return (
    <section className="border-b" aria-labelledby="results-hero-title">
      <div className="content-shell grid gap-10 py-16 sm:py-20 lg:grid-cols-[1.25fr_0.75fr] lg:py-24">
        <div>
          <p className="eyebrow">Results explorer</p>
          <h1 id="results-hero-title" className="mt-4 text-5xl font-semibold tracking-tight sm:text-6xl">Benchmark results</h1>
          <p className="mt-5 text-xl text-foreground">Compare tasks solved, time spent, and strength of evidence.</p>
          <p className="mt-4 max-w-2xl leading-7 text-muted-foreground">The comparison below starts with the current 29-task corpus. Historical results remain available, but are never mixed into the same ranking.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild variant="secondary">
              <a href="https://github.com/maximilianpw/nixbench/releases/download/2.0.0/nixbench-2.0.0-calibration-evidence.tar.zst">
                <DownloadIcon data-icon="inline-start" />
                Download 2.0 calibration evidence
              </a>
            </Button>
            <Button asChild variant="ghost">
              <a href="https://github.com/maximilianpw/nixbench/releases/tag/2.0.0">
                Release notes and checksum
                <ExternalLinkIcon data-icon="inline-end" />
              </a>
            </Button>
          </div>
          <div className="mt-5 flex flex-wrap gap-3 text-sm" aria-label="Current corpus coverage">
            <span className="rounded-md bg-nix-blue-soft px-3 py-2 font-semibold text-accent-foreground">Current 29-task corpus</span>
            <strong className="rounded-md border px-3 py-2">{currentEvidenceSummary.configurations} configurations</strong>
            <b className="rounded-md border px-3 py-2">{currentEvidenceSummary.trials} recorded runs</b>
          </div>
        </div>
        <div className="self-end">
          <span className="eyebrow">All recorded datasets</span>
          <StatGrid items={resultOverviewStats} label="All recorded dataset totals" className="mt-4" />
        </div>
      </div>
    </section>
  );
}
