import { ArrowDown, ArrowRight, TerminalSquare } from "lucide-react";

import {
  InlineSeparator,
  InsightCard,
  MethodStep,
  PageSection,
  SectionHeader,
  StatGrid,
} from "@/components/benchmark/BenchmarkPrimitives";
import { LeaderboardPanel } from "@/components/charts/LeaderboardPanel";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  difficultyDistribution,
  explainerCards,
  heroStats,
  methodSteps,
  taskExamples,
} from "@/data/benchmark";

function HomeHero() {
  return (
    <section className="product-hero">
      <div className="product-hero-inner">
        <div className="hero-copy">
          <Badge variant="codex">v0.2 benchmark corpus</Badge>
          <div className="title-row">
            <span className="title-mark" aria-hidden="true">
              λ
            </span>
            <h1>NixBench</h1>
          </div>
          <p className="byline">agentic Nix benchmark</p>
          <p className="hero-lede">
            Objective Nix repair tasks for AI coding agents, scored by hidden shell evaluators and preserved as
            diff-backed run artifacts.
          </p>
          <div className="actions" aria-label="Page actions">
            <Button asChild>
              <a href="results.html">
                Compare results <ArrowRight data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
            <Button asChild variant="secondary">
              <a href="https://github.com/maximilianpw/nixbench#quick-start">
                Run locally <TerminalSquare data-icon="inline-end" aria-hidden="true" />
              </a>
            </Button>
          </div>
          <a className="inline-jump" href="#tasks">
            Inspect the task corpus <ArrowDown data-icon="inline-end" aria-hidden="true" />
          </a>
        </div>

        <div className="benchmark-specimen" aria-label="Benchmark run artifact preview">
          <div className="specimen-header">
            <span>results/20260625T073228Z-a5a4a383</span>
            <Badge variant="pass">22/26 pass</Badge>
          </div>
          <StatGrid items={heroStats} label="Benchmark summary" className="hero-stat-grid" />
          <InlineSeparator />
          <div className="specimen-rows" aria-hidden="true">
            <span className="trace-line pass">module-system-boundaries</span>
            <span className="trace-line pass">python-cuda-uv2nix-patch</span>
            <span className="trace-line fail">debug-network-false-lead</span>
            <span className="trace-line pass">flake-per-system-outputs</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function ExplainerSection() {
  return (
    <PageSection className="explainer-section" labelledBy="why-heading">
      <div className="narrative">
        <p className="eyebrow">Why this exists</p>
        <h2 id="why-heading">Plausible Nix often fails at evaluation time.</h2>
        <p>
          The benchmark gives agents a copied starter tree, a prompt, and no access to the hidden evaluator. It rewards
          final worktree behavior, not a fluent explanation of what the code should do.
        </p>
      </div>
      <div className="insight-grid">
        {explainerCards.map((card) => (
          <InsightCard key={card.title} eyebrow={card.kicker} title={card.title} description={card.description} />
        ))}
      </div>
    </PageSection>
  );
}

function TasksSection() {
  return (
    <PageSection id="tasks" className="tasks-section" labelledBy="tasks-heading">
      <SectionHeader
        eyebrow="Task examples"
        title="Twenty-six small repositories, one hidden evaluator each."
        headingId="tasks-heading"
        action={{ href: "https://github.com/maximilianpw/nixbench#what-it-measures", label: "All 26 tasks" }}
      />

      <div className="task-grid">
        {taskExamples.map((task) => (
          <Card key={task.title} className="task-card">
            <CardHeader>
              <Badge variant="default">{task.area}</Badge>
              <CardTitle>{task.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{task.description}</CardDescription>
            </CardContent>
            <CardFooter>
              <span>difficulty</span>
              <strong>{task.difficulty}</strong>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="difficulty-strip" aria-label="Difficulty distribution">
        {difficultyDistribution.map(([count, description]) => (
          <Card key={count} className="distribution-card">
            <CardHeader>
              <CardTitle>{count}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </PageSection>
  );
}

function MethodSection() {
  return (
    <PageSection className="method-section" labelledBy="method-heading">
      <SectionHeader
        eyebrow="Methodology"
        title="The agent edits a worktree. The evaluator scores the result."
        headingId="method-heading"
        action={{ href: "docs/running-agents.md", label: "Run guide" }}
      />
      <ol className="method-list">
        {methodSteps.map(([label, description]) => (
          <MethodStep key={label} label={label} description={description} />
        ))}
      </ol>
    </PageSection>
  );
}

function UpdatesSection() {
  return (
    <section className="cta-band" id="updates" aria-labelledby="updates-heading">
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

export function HomePage() {
  return (
    <main className="app-page home-page">
      <HomeHero />
      <LeaderboardPanel />
      <ExplainerSection />
      <TasksSection />
      <MethodSection />
      <UpdatesSection />
    </main>
  );
}
