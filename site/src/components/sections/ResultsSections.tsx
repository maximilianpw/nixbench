import { TimingChart } from "@/components/charts/TimingChart";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  failureNotes,
  modelRunCards,
  resultStats,
  resultColumns,
  taskResults,
  verdicts,
  type TaskRunCell,
  type TaskStatus,
} from "@/data/benchmark";

export function ResultsHero() {
  return (
    <section className="detail-hero">
      <div className="detail-hero-inner">
        <div>
          <p className="eyebrow">Model comparison · June 24-25, 2026</p>
          <h1>GPT and Claude model runs on the full 26-task NixBench corpus.</h1>
          <p>
            GPT-5.5 and GPT-5.4 were swept across reasoning effort levels, while GPT-5.4 mini and Claude Opus 4.8
            remain xhigh/default baselines under the same 240 second per-task timeout.
          </p>
        </div>
        <dl className="result-stats" aria-label="Baseline summary">
          {resultStats.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export function ResultsSummary() {
  return (
    <section className="section results-summary" aria-labelledby="summary-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Run summary</p>
          <h2 id="summary-heading">Two rows reached 22 passes on the 26-task corpus.</h2>
        </div>
        <a className="text-link" href="docs/runs/2026-06-24-model-comparison.md">
          Source notes
        </a>
      </div>

      <div className="verdict-strip" aria-label="Run observations">
        {verdicts.map((verdict) => (
          <article key={verdict.label}>
            <span>{verdict.label}</span>
            <strong>{verdict.value}</strong>
            <p>{verdict.description}</p>
          </article>
        ))}
      </div>

      <div className="run-card-grid">
        {modelRunCards.map((run) => (
          <Card key={run.runId} className={`run-card ${run.kind}-card`}>
            <div className="run-card-head">
              <h3>{run.agent}</h3>
              <span>
                {run.status}
                <br />
                {run.runId}
              </span>
            </div>
            <p className="run-score">
              {run.score}
              <span>/{run.maxScore}</span>
            </p>
            <dl className="metric-list">
              {run.metrics.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </Card>
        ))}
      </div>
    </section>
  );
}

function StatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge variant={status} className={`status ${status}`}>
      {status === "pass" ? "Pass" : "Fail"}
    </Badge>
  );
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
    <>
      <StatusBadge status={cell.status} /> {cell.seconds == null ? "..." : `${cell.seconds.toFixed(1)}s`}
    </>
  );
}

export function TaskResultsSection() {
  return (
    <section className="section task-results" aria-labelledby="task-results-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Per-task outcomes</p>
          <h2 id="task-results-heading">Baseline outcomes are shown task by task.</h2>
        </div>
      </div>
      <div className="result-table-wrap">
        <table className="result-table">
          <thead>
            <tr>
              <th scope="col">Task</th>
              <th scope="col">Area</th>
              {resultColumns.map((column) => (
                <th key={column.key} scope="col">
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {taskResults.map((task) => (
              <tr
                key={task.task}
                className={taskOutcomeClass(resultColumns.map((column) => task.results[column.key]))}
              >
                <td>
                  <code>{task.task}</code>
                </td>
                <td>{task.area}</td>
                {resultColumns.map((column) => (
                  <td key={column.key}>
                    <ResultCell cell={task.results[column.key]} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export { TimingChart };

export function FailureSection() {
  return (
    <section className="section failure-section" aria-labelledby="failure-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Outcome notes</p>
          <h2 id="failure-heading">Several outcome patterns repeat across runs.</h2>
        </div>
      </div>
      <div className="advances-grid">
        {failureNotes.map((note) => (
          <Card key={note.title}>
            <span className="kicker">{note.kicker}</span>
            <h3>{note.title}</h3>
            <p>{note.description}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}
