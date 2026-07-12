import { useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { ResultCell } from "@/components/pages/results/ResultCell";
import { taskOutcomeClass } from "@/components/pages/results/taskOutcomeClass";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { modelTaskSummaries, resultColumns, taskResults, type ModelKey } from "@/data/benchmark";

export type TaskResultsSectionProps = {};

type ModelSelection = "all" | ModelKey;

export function TaskResultsSection({}: TaskResultsSectionProps = {}) {
  const [selectedModel, setSelectedModel] = useState<ModelSelection>("all");
  const visibleColumns =
    selectedModel === "all" ? resultColumns : resultColumns.filter((column) => column.key === selectedModel);
  const visibleSummaries =
    selectedModel === "all"
      ? modelTaskSummaries
      : modelTaskSummaries.filter((summary) => summary.key === selectedModel);

  return (
    <PageSection className="task-results" labelledBy="task-results-heading">
      <SectionHeader
        eyebrow="Baseline matrix"
        title="Every task, shown against fixed baseline runs."
        description="These are named comparison runs—not each model’s best row. Codex columns use xhigh effort; the historical Claude column preserves the original default composite."
        headingId="task-results-heading"
      />

      <div className="matrix-toolbar">
        <ToggleGroup
          type="single"
          value={selectedModel}
          onValueChange={(value) => {
            if (value) setSelectedModel(value as ModelSelection);
          }}
          aria-label="Visible model columns"
          className="model-toggle"
        >
          <ToggleGroupItem value="all" aria-label="Show all model columns">
            All
          </ToggleGroupItem>
          {resultColumns.map((column) => (
            <ToggleGroupItem key={column.key} value={column.key} aria-label={`Show ${column.label}`}>
              {column.shortLabel}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <p>
          Showing <strong>{visibleColumns.length}</strong> of <strong>{resultColumns.length}</strong> model columns
        </p>
      </div>

      <div className="baseline-context">
        <strong>Comparison context</strong>
        <span>Historical 26-task and current 29-task baselines · 240-second per-task timeout</span>
        <small>Rows marked (+2) combine a 24-task run with two supplemental task artifacts.</small>
        <a href="docs/runs/2026-06-24-model-comparison.html">Inspect run provenance</a>
      </div>

      <div className="matrix-summary-grid">
        {visibleSummaries.map((summary) => (
          <Card key={summary.key} className="matrix-summary-card">
            <CardHeader>
              <CardTitle>{summary.shortLabel}</CardTitle>
              <CardDescription>
                {summary.label} · {summary.corpus} · {summary.effort}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="matrix-summary-score">
                <span>{summary.passLabel}</span>
                <small>{summary.failed} failed</small>
              </div>
              <Progress value={summary.passRate} aria-label={`${summary.label} task pass rate`} />
              <p>Average task time: {summary.averageTimeLabel}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Table className="result-table" containerClassName="result-table-wrap" aria-label="Per-task model outcomes">
        <TableCaption>Pass/fail status and elapsed task seconds for the selected model columns.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Task</TableHead>
            <TableHead scope="col">Area</TableHead>
            {visibleColumns.map((column) => (
              <TableHead key={column.key} scope="col">
                <span>{column.label}</span>
                <small>
                  {column.corpus} · {column.effort}
                </small>
                <code>{column.runId}</code>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {taskResults.map((task) => (
            <TableRow
              key={task.task}
              className={taskOutcomeClass(visibleColumns.map((column) => task.results[column.key]))}
            >
              <TableHead scope="row">
                <code>{task.task}</code>
              </TableHead>
              <TableCell>{task.area}</TableCell>
              {visibleColumns.map((column) => (
                <TableCell key={column.key}>
                  <ResultCell cell={task.results[column.key]} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </PageSection>
  );
}
