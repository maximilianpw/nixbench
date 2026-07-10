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
        eyebrow="Per-task outcomes"
        title="Compare the task matrix across all model columns."
        description="Use the model switcher to focus the table when the dataset grows beyond the currently visible columns."
        headingId="task-results-heading"
      />

      <div className="matrix-toolbar" aria-label="Task matrix controls">
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

      <div className="matrix-summary-grid" aria-label="Selected model task summaries">
        {visibleSummaries.map((summary) => (
          <Card key={summary.key} className="matrix-summary-card">
            <CardHeader>
              <CardTitle>{summary.shortLabel}</CardTitle>
              <CardDescription>{summary.label}</CardDescription>
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
              <TableCell>
                <code>{task.task}</code>
              </TableCell>
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
