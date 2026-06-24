import { TimingChart } from "@/components/charts/TimingChart";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  baselineRunCards,
  failureNotes,
  resultStats,
  taskResults,
  verdicts,
  type TaskResult,
} from "@/data/benchmark";

export function ResultsHero() {
  return (
    <section className="detail-hero">
      <div className="detail-hero-inner">
        <div>
          <p className="eyebrow">Baseline run · June 23, 2026</p>
          <h1>Codex CLI vs Claude CLI on the initial ten-task corpus.</h1>
          <p>
            The first comparable NixBench runs tied at 500/1000. Claude used less agent time overall; each agent solved
            one task the other missed.
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
          <p className="eyebrow">Scoreboard</p>
          <h2 id="summary-heading">Same score, different failure shape.</h2>
        </div>
        <a className="text-link" href="docs/runs/2026-06-23-agent-baseline.md">
          Source notes
        </a>
      </div>

      <div className="verdict-strip" aria-label="Comparison verdict">
        {verdicts.map((verdict) => (
          <article key={verdict.label}>
            <span>{verdict.label}</span>
            <strong>{verdict.value}</strong>
            <p>{verdict.description}</p>
          </article>
        ))}
      </div>

      <div className="run-card-grid">
        {baselineRunCards.map((run) => (
          <Card key={run.agent} className={`run-card ${run.kind}-card`}>
            <div className="run-card-head">
              <h3>{run.agent}</h3>
              <span>{run.runId}</span>
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

function StatusBadge({ status }: { status: "pass" | "fail" }) {
  return (
    <Badge variant={status} className={`status ${status}`}>
      {status === "pass" ? "Pass" : "Fail"}
    </Badge>
  );
}

function outcomeClass(outcome: TaskResult["outcome"]) {
  return `outcome-${outcome}`;
}

export function TaskResultsSection() {
  return (
    <section className="section task-results" aria-labelledby="task-results-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Per-task outcomes</p>
          <h2 id="task-results-heading">The tie was not identical.</h2>
        </div>
      </div>
      <div className="result-table-wrap">
        <table className="result-table">
          <thead>
            <tr>
              <th scope="col">Task</th>
              <th scope="col">Area</th>
              <th scope="col">Codex</th>
              <th scope="col">Claude</th>
              <th scope="col">Readout</th>
            </tr>
          </thead>
          <tbody>
            {taskResults.map((task) => (
              <tr key={task.task} className={outcomeClass(task.outcome)}>
                <td>
                  <code>{task.task}</code>
                </td>
                <td>{task.area}</td>
                <td>
                  <StatusBadge status={task.codex} /> {task.codexSeconds.toFixed(1)}s
                </td>
                <td>
                  <StatusBadge status={task.claude} /> {task.claudeSeconds.toFixed(1)}s
                </td>
                <td>{task.readout}</td>
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
          <p className="eyebrow">Failure notes</p>
          <h2 id="failure-heading">The hard cases were fake-lib and hidden-shape traps.</h2>
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
