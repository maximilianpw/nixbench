import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { currentCorpusTaskCount, difficultyDistribution, taskExamples, taskResults } from "@/data/benchmark";

export function TasksSection() {
  const [query, setQuery] = useState("");
  const visibleTasks = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) return taskResults;
    return taskResults.filter((task) => `${task.task} ${task.area}`.toLowerCase().includes(normalizedQuery));
  }, [query]);

  return (
    <PageSection id="tasks" labelledBy="tasks-heading">
      <SectionHeader title={`${currentCorpusTaskCount} repository-repair tasks`} description="Browse the full corpus across modules, flakes, packaging, fetchers, overlays, and shell integration." headingId="tasks-heading" />

      <div className="grid gap-4 md:grid-cols-3">
        {taskExamples.slice(0, 3).map((task) => (
          <Card key={task.title}>
            <CardHeader><CardTitle>{task.title}</CardTitle></CardHeader>
            <CardContent><CardDescription>{task.description}</CardDescription></CardContent>
            <CardFooter className="mt-auto justify-between border-t pt-5 font-mono text-xs uppercase tracking-wider text-muted-foreground"><span>difficulty</span><strong className="text-foreground">{task.difficulty}</strong></CardFooter>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        {difficultyDistribution.map(([count, description]) => (
          <Card key={count} className="gap-3 py-5">
            <CardHeader><CardTitle className="font-mono text-2xl text-nix-blue">{count}</CardTitle></CardHeader>
            <CardContent><CardDescription>{description}</CardDescription></CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-10 rounded-lg border bg-card p-4 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label className="flex min-h-11 flex-1 items-center gap-3 rounded-md border bg-background px-3 focus-within:ring-2 focus-within:ring-ring">
            <span className="sr-only">Search benchmark tasks</span>
            <Search className="size-4 text-muted-foreground" aria-hidden="true" />
            <input className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground" type="search" value={query} onChange={(event) => setQuery(event.currentTarget.value)} placeholder="Search all tasks or areas" />
          </label>
          <p className="font-mono text-xs text-muted-foreground" aria-live="polite">{visibleTasks.length} tasks shown</p>
        </div>
        <ul className="mt-5 grid gap-px overflow-hidden rounded-md border bg-border sm:grid-cols-2 lg:grid-cols-3">
          {visibleTasks.map((task) => (
            <li className="bg-card" key={task.task}>
              <a className="flex min-h-20 flex-col justify-center gap-1 p-4 no-underline hover:bg-muted" href={`https://github.com/maximilianpw/nixbench/tree/main/tasks/${task.task}`}>
                <strong className="text-sm">{formatTaskName(task.task)}</strong>
                <span className="font-mono text-xs text-muted-foreground">{task.area}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </PageSection>
  );
}

function formatTaskName(task: string) {
  return task.split("-").map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}
