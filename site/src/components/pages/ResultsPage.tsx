import {
  InsightCard,
  PageSection,
  ScoreCard,
  SectionHeader,
  StatGrid,
} from "@/components/benchmark/BenchmarkPrimitives";
import { TimingChart } from "@/components/charts/TimingChart";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  failureNotes,
  modelRunCards,
  resultColumns,
  resultStats,
  taskResults,
  verdicts,
  type TaskRunCell,
  type TaskStatus,
} from "@/data/benchmark";

function ResultsHero() {
  return (
    <section className="results-hero">
      <div className="results-hero-inner">
        <div>
          <Badge variant="codex">Model comparison</Badge>
          <p className="eyebrow">June 24-28, 2026</p>
          <h1>GPT and Claude model runs on the full 26-task NixBench corpus.</h1>
          <p>
            GPT-5.5 and GPT-5.4 were swept across reasoning effort levels, while GPT-5.4 mini and Claude Opus 4.8
            remain baseline comparisons under the same 240 second per-task timeout.
          </p>
        </div>
        <StatGrid items={resultStats} label="Baseline summary" className="result-stat-grid" />
      </div>
    </section>
  );
}

function ResultsSummary() {
  return (
    <PageSection className="results-summary" labelledBy="summary-heading">
      <SectionHeader
        eyebrow="Run summary"
        title="Two rows reached 22 passes on the 26-task corpus."
        headingId="summary-heading"
        action={{ href: "docs/runs/2026-06-24-model-comparison.md", label: "Source notes" }}
      />

      <div className="verdict-grid" aria-label="Run observations">
        {verdicts.map((verdict) => (
          <Card key={verdict.label} className="verdict-card">
            <CardHeader>
              <Badge variant="default">{verdict.label}</Badge>
              <CardTitle>{verdict.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{verdict.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="run-card-grid">
        {modelRunCards.map((run) => (
          <ScoreCard
            key={run.runId}
            title={run.agent}
            eyebrow={run.status}
            value={run.score}
            max={run.maxScore}
            badgeVariant={run.kind}
            description={run.runId}
            metrics={run.metrics}
          />
        ))}
      </div>
    </PageSection>
  );
}

function StatusBadge({ status }: { status: TaskStatus }) {
  return <Badge variant={status}>{status === "pass" ? "Pass" : "Fail"}</Badge>;
}

function taskOutcomeClass(cells: TaskRunCell[]) {
  if (cells.every((cell) => cell.status === "pass")) {
    return "outcome-mutual-pass";
  }
  if (cells.every((cell) => cell.status === "fail")) {
    return "outcome-mutual-fail";
  }
  return "outcome-split";
}

function ResultCell({ cell }: { cell: TaskRunCell }) {
  return (
    <span className="result-cell">
      <StatusBadge status={cell.status} />
      <span>{cell.seconds == null ? "..." : `${cell.seconds.toFixed(1)}s`}</span>
    </span>
  );
}

function TaskResultsSection() {
  return (
    <PageSection className="task-results" labelledBy="task-results-heading">
      <SectionHeader
        eyebrow="Per-task outcomes"
        title="Baseline outcomes are shown task by task."
        headingId="task-results-heading"
      />
      <div className="table-wrapper result-table-wrap">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Task</TableHead>
              <TableHead scope="col">Area</TableHead>
              {resultColumns.map((column) => (
                <TableHead key={column.key} scope="col">
                  {column.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {taskResults.map((task) => (
              <TableRow
                key={task.task}
                className={taskOutcomeClass(resultColumns.map((column) => task.results[column.key]))}
              >
                <TableCell>
                  <code>{task.task}</code>
                </TableCell>
                <TableCell>{task.area}</TableCell>
                {resultColumns.map((column) => (
                  <TableCell key={column.key}>
                    <ResultCell cell={task.results[column.key]} />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </PageSection>
  );
}

function TimingSection() {
  return (
    <PageSection className="timing-section" labelledBy="timing-heading">
      <SectionHeader
        eyebrow="Agent duration"
        title="The xhigh/default baselines show the per-task time profile."
        headingId="timing-heading"
      />
      <TimingChart />
    </PageSection>
  );
}

function FailureSection() {
  return (
    <PageSection className="failure-section" labelledBy="failure-heading">
      <SectionHeader
        eyebrow="Outcome notes"
        title="Several outcome patterns repeat across runs."
        headingId="failure-heading"
      />
      <div className="insight-grid">
        {failureNotes.map((note) => (
          <InsightCard key={note.title} eyebrow={note.kicker} title={note.title} description={note.description} />
        ))}
      </div>
    </PageSection>
  );
}

export function ResultsPage() {
  return (
    <main className="app-page results-page">
      <ResultsHero />
      <ResultsSummary />
      <TaskResultsSection />
      <TimingSection />
      <FailureSection />
    </main>
  );
}
