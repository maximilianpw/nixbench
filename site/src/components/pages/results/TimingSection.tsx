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
    <PageSection className="timing-section" labelledBy="timing-heading">
      <SectionHeader
        eyebrow="Baseline timing"
        title="Elapsed task time for the same fixed baseline runs."
        description="Timing follows the exact columns above: xhigh Codex runs and the historical Claude default composite, each with a 240-second per-task timeout."
        headingId="timing-heading"
      />
      <div className="matrix-toolbar timing-toolbar">
        <ToggleGroup
          type="single"
          value={selectedModel}
          onValueChange={(value) => {
            if (value) setSelectedModel(value as TimingSelection);
          }}
          aria-label="Timing chart model columns"
          className="model-toggle"
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
        <p>
          Charting <strong>{visibleColumns.length}</strong> of <strong>{resultColumns.length}</strong> model columns
        </p>
      </div>
      <details className="timing-provenance">
        <summary>Run provenance ({visibleColumns.length})</summary>
        <ul>
          {visibleColumns.map((column) => (
            <li key={column.key}>
              <strong>{column.label}</strong>
              <span>
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
