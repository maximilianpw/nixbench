import { ArrowDown, ArrowRight } from "lucide-react";

import { LeaderboardPanel } from "@/components/charts/LeaderboardPanel";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  difficultyDistribution,
  explainerCards,
  heroStats,
  methodSteps,
  taskExamples,
} from "@/data/benchmark";

export function Masthead() {
  return (
    <section className="masthead">
      <div className="masthead-inner">
        <div className="masthead-top">
          <div className="title-block">
            <div className="title-row">
              <span className="title-mark" aria-hidden="true">
                λ
              </span>
              <h1>NixBench</h1>
            </div>
            <p className="byline">agentic Nix benchmark</p>
          </div>
          <dl className="hero-stats" aria-label="Benchmark summary">
            {heroStats.map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="masthead-bottom">
          <p>
            Measuring AI coding agents on long-horizon Nix repository repair tasks with hidden shell evaluators and
            concrete worktree diffs.
          </p>
          <div className="actions" aria-label="Page actions">
            <Button asChild>
              <a href="results.html">
                Compare results <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
            <Button asChild variant="secondary">
              <a href="https://github.com/maximilianpw/nixbench#quick-start">Run locally</a>
            </Button>
          </div>
        </div>
        <a className="inline-jump" href="#tasks">
          Inspect the task corpus <ArrowDown data-icon="inline-end" aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}

export { LeaderboardPanel };

export function ExplainerSection() {
  return (
    <section className="section explainer-section" aria-labelledby="why-heading">
      <div className="narrative">
        <h2 id="why-heading">NixBench exists because plausible Nix often fails at evaluation time.</h2>
        <p>
          The benchmark gives agents a copied starter tree, a prompt, and no access to the hidden evaluator. It rewards
          final worktree behavior, not a fluent explanation of what the code should do.
        </p>
      </div>
      <div className="advances-grid">
        {explainerCards.map((card) => (
          <Card key={card.title}>
            <span className="kicker">{card.kicker}</span>
            <h3>{card.title}</h3>
            <p>{card.description}</p>
          </Card>
        ))}
      </div>
    </section>
  );
}

export function TasksSection() {
  return (
    <section className="section tasks-section" id="tasks" aria-labelledby="tasks-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Task examples</p>
          <h2 id="tasks-heading">Twenty-four small repositories, one hidden evaluator each.</h2>
        </div>
        <a className="text-link" href="https://github.com/maximilianpw/nixbench#what-it-measures">
          All 24 tasks
        </a>
      </div>

      <div className="task-grid">
        {taskExamples.map((task) => (
          <Card key={task.title} className="task-card">
            <h3>{task.title}</h3>
            <p>{task.description}</p>
            <footer>
              <span>{task.area}</span>
              <strong>{task.difficulty}</strong>
            </footer>
          </Card>
        ))}
      </div>

      <div className="difficulty-strip" aria-label="Difficulty distribution">
        {difficultyDistribution.map(([count, description]) => (
          <article key={count}>
            <span>{count}</span>
            <p>{description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function MethodSection() {
  return (
    <section className="section method-section" aria-labelledby="method-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Methodology</p>
          <h2 id="method-heading">The agent edits a worktree. The evaluator scores the result.</h2>
        </div>
        <a className="text-link" href="docs/running-agents.md">
          Run guide
        </a>
      </div>
      <ol className="method-list">
        {methodSteps.map(([label, description]) => (
          <li key={label}>
            <span>{label}</span>
            <p>{description}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function UpdatesSection() {
  return (
    <section className="updates-section" id="updates" aria-labelledby="updates-heading">
      <div>
        <p className="eyebrow">Run your agent</p>
        <h2 id="updates-heading">Add another row to the benchmark.</h2>
        <p>Use the local harness to run a CLI agent against the same copied worktree contract and hidden evaluator shape.</p>
      </div>
      <Button asChild>
        <a href="https://github.com/maximilianpw/nixbench#running-with-codex">
          Open run command <ArrowRight data-icon="inline-end" aria-hidden="true" />
        </a>
      </Button>
    </section>
  );
}
