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
    <PageSection labelledBy="task-results-heading">
      <SectionHeader
        title="Every task, shown against fixed baseline runs."
        description="These are named comparison runs—not each model’s best row. Codex columns use xhigh effort; the historical Claude column preserves the original default composite."
        headingId="task-results-heading"
      />

      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <ToggleGroup
          type="single"
          value={selectedModel}
          onValueChange={(value) => {
            if (value) setSelectedModel(value as ModelSelection);
          }}
          aria-label="Visible model columns"
          className="max-sm:w-full"
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
        <p className="font-mono text-xs text-muted-foreground">
          Showing <strong>{visibleColumns.length}</strong> of <strong>{resultColumns.length}</strong> model columns
        </p>
      </div>

      <div className="mb-6 grid gap-1 rounded-lg border bg-muted/50 p-4 text-sm">
        <strong>Comparison context</strong>
        <span className="text-muted-foreground">Historical 26-task and current 29-task baselines · 240-second per-task timeout</span>
        <small className="text-muted-foreground">Rows marked (+2) combine a 24-task run with two supplemental task artifacts.</small>
        <a className="mt-2 w-fit font-semibold text-nix-blue" href="docs/runs/2026-06-24-model-comparison.html">Inspect run provenance</a>
      </div>

      <div className="mb-8 grid gap-4 md:grid-cols-3">
        {visibleSummaries.map((summary) => (
          <Card key={summary.key}>
            <CardHeader>
              <CardTitle>{summary.shortLabel}</CardTitle>
              <CardDescription>
                {summary.label} · {summary.corpus} · {summary.effort}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-3 flex items-end justify-between">
                <span className="text-2xl font-semibold">{summary.passLabel}</span>
                <small className="text-muted-foreground">{summary.failed} failed</small>
              </div>
              <Progress value={summary.passRate} aria-label={`${summary.label} task pass rate`} />
              <p className="mt-3 text-sm text-muted-foreground">Average task time: {summary.averageTimeLabel}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Table className="min-w-[760px]" aria-label="Per-task model outcomes">
        <TableCaption>Pass/fail status and elapsed task seconds for the selected model columns.</TableCaption>
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Task</TableHead>
            <TableHead scope="col">Area</TableHead>
            {visibleColumns.map((column) => (
              <TableHead key={column.key} scope="col">
                <span className="block text-foreground">{column.label}</span>
                <small className="mt-1 block normal-case tracking-normal">
                  {column.corpus} · {column.effort}
                </small>
                <code className="mt-1 block w-fit normal-case tracking-normal">{column.runId}</code>
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
                <code className="whitespace-nowrap">{task.task}</code>
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
