import { useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { TimingChart } from "@/components/charts/TimingChart";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { resultColumns, type ModelKey } from "@/data/benchmark";

export type TimingSectionProps = {};

type TimingSelection = "all" | ModelKey;

export function TimingSection({}: TimingSectionProps = {}) {
  const [selectedModel, setSelectedModel] = useState<TimingSelection>("all");
  const visibleColumns =
    selectedModel === "all" ? resultColumns : resultColumns.filter((column) => column.key === selectedModel);

  return (
    <PageSection labelledBy="timing-heading">
      <SectionHeader
        title="Elapsed task time for the same fixed baseline runs."
        description="Timing follows the exact columns above: xhigh Codex runs and the historical Claude default composite, each with a 240-second per-task timeout."
        headingId="timing-heading"
      />
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <ToggleGroup
          type="single"
          value={selectedModel}
          onValueChange={(value) => {
            if (value) setSelectedModel(value as TimingSelection);
          }}
          aria-label="Timing chart model columns"
          className="max-sm:w-full"
        >
          <ToggleGroupItem value="all" aria-label="Show all timing columns">
            All
          </ToggleGroupItem>
          {resultColumns.map((column) => (
            <ToggleGroupItem key={column.key} value={column.key} aria-label={`Show ${column.label} timing`}>
              {column.shortLabel}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <p className="font-mono text-xs text-muted-foreground">
          Charting <strong>{visibleColumns.length}</strong> of <strong>{resultColumns.length}</strong> model columns
        </p>
      </div>
      <details className="mb-6 rounded-lg border bg-card p-4 text-sm">
        <summary className="cursor-pointer font-semibold">Run provenance ({visibleColumns.length})</summary>
        <ul className="mt-4 grid gap-3">
          {visibleColumns.map((column) => (
            <li className="grid gap-1 border-t pt-3 sm:grid-cols-[1fr_1fr_2fr]" key={column.key}>
              <strong>{column.label}</strong>
              <span className="text-muted-foreground">
                {column.corpus} · {column.effort}
              </span>
              <code>{column.runId}</code>
            </li>
          ))}
        </ul>
      </details>
      <TimingChart columns={visibleColumns} />
    </PageSection>
  );
}
