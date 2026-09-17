import { useMemo, useState } from "react";
import { ArrowUpDown } from "lucide-react";

import { modelColors } from "@/components/charts/model-colors";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatDuration, type LeaderboardAggregate, type ModelKey } from "@/data/benchmark";

export type LeaderboardTableProps = {
  aggregates: LeaderboardAggregate[];
  highlightedModel: ModelKey | null;
  onHighlightedModelChange: (model: ModelKey | null) => void;
};

type SortKey = "configuration" | "effort" | "trialCount" | "tasksPassed" | "secondsPerTask" | "timeouts";
type SortDirection = "asc" | "desc";
type SortState = { key: SortKey; direction: SortDirection };

const defaultSort: SortState = { key: "configuration", direction: "asc" };
const effortRank = { default: -1, low: 0, medium: 1, high: 2, xhigh: 3, max: 4, ultra: 5 } as const;

export function LeaderboardTable({
  aggregates,
  highlightedModel,
  onHighlightedModelChange,
}: LeaderboardTableProps) {
  const [sort, setSort] = useState<SortState>(defaultSort);
  const sortedAggregates = useMemo(() => sortAggregates(aggregates, sort), [aggregates, sort]);
  const mobileGroups = useMemo(() => groupAggregatesByModel(aggregates), [aggregates]);

  const toggleSort = (key: SortKey) => {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "desc" ? "asc" : "desc",
    }));
  };

  const ariaSortFor = (key: SortKey) => {
    if (sort.key !== key) return undefined;
    return sort.direction === "asc" ? "ascending" : "descending";
  };

  return (
    <>
      <Table
        className="min-w-[980px]"
        containerClassName="hidden md:block"
        aria-label="NixBench configuration evidence"
      >
        <TableHeader>
          <TableRow>
            <TableHead scope="col" aria-sort={ariaSortFor("configuration")}>
              <SortButton label="Configuration" sortKey="configuration" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("effort")}>
              <SortButton label="Effort" sortKey="effort" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("trialCount")}>
              <SortButton label="Evidence" sortKey="trialCount" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("tasksPassed")}>
              <SortButton label="Mean tasks" sortKey="tasksPassed" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col">95% CI / observed</TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("secondsPerTask")}>
              <SortButton label="Seconds / task" sortKey="secondsPerTask" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("timeouts")}>
              <SortButton label="Timeouts" sortKey="timeouts" sort={sort} onSort={toggleSort} />
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody onPointerLeave={() => onHighlightedModelChange(null)}>
          {sortedAggregates.map((aggregate) => (
            <TableRow
              key={aggregate.id}
              data-highlighted={highlightedModel === aggregate.series || undefined}
              data-dimmed={(highlightedModel !== null && highlightedModel !== aggregate.series) || undefined}
              onPointerEnter={() => onHighlightedModelChange(aggregate.series ?? null)}
            >
              <TableHead scope="row">
                <span className="flex min-w-64 items-center gap-3">
                  <span className="flex size-8 shrink-0 items-center justify-center rounded-md border font-mono text-xs font-bold" style={{ borderColor: agentColor(aggregate), color: agentColor(aggregate) }} aria-hidden="true">
                    {aggregate.marker}
                  </span>
                  <span className="flex flex-col text-left normal-case tracking-normal">
                    <strong className="font-sans text-sm text-foreground">{primaryAgentName(aggregate.agent)}</strong>
                    <small className="font-sans text-xs font-normal text-muted-foreground">
                      {agentDetails(aggregate.agent)}{agentDetails(aggregate.agent) ? " · " : ""}{aggregate.trialCount} recorded {aggregate.trialCount === 1 ? "run" : "runs"}
                    </small>
                  </span>
                </span>
              </TableHead>
              <TableCell><Badge variant="default">{aggregate.effort ?? "default"}</Badge></TableCell>
              <TableCell>
                <Badge variant={aggregate.trialCount > 1 ? "pass" : "muted"}>
                  {aggregate.provenance === "composite"
                    ? "legacy composite"
                    : aggregate.trialCount > 1
                      ? `n=${aggregate.trialCount}`
                      : "single run"}
                </Badge>
              </TableCell>
              <TableCell>
                <span className="mb-2 block font-mono text-xs font-semibold tabular-nums">{aggregate.passedTasks.mean.toFixed(1)} / {aggregate.taskCount}</span>
                <Progress
                  value={(aggregate.passedTasks.mean / aggregate.taskCount) * 100}
                  aria-label={`${aggregate.agent} ${aggregate.effort ?? "default"} mean tasks passed`}
                />
              </TableCell>
              <TableCell>
                <span className="flex flex-col">
                  <strong className="font-mono text-xs tabular-nums">{formatInterval(aggregate)}</strong>
                  <small className="text-muted-foreground">observed {aggregate.passedTasks.min.toFixed(0)}–{aggregate.passedTasks.max.toFixed(0)}</small>
                </span>
              </TableCell>
              <TableCell>
                <span className="flex flex-col">
                  <strong className="font-mono text-xs tabular-nums">{aggregate.agentSecondsPerTask.mean.toFixed(1)}s</strong>
                  <small className="text-muted-foreground">{formatDuration(aggregate.agentTimeSeconds.mean)} / corpus</small>
                </span>
              </TableCell>
              <TableCell>{aggregate.totalTimeouts}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <ol className="grid gap-4 md:hidden" aria-label="NixBench results grouped by model">
        {mobileGroups.map((group) => (
          <li className="overflow-hidden rounded-lg border bg-card" key={group.key}>
            <div className="flex items-center gap-3 border-b bg-muted/40 p-4">
              <span className="flex size-8 items-center justify-center rounded-md border font-mono text-xs font-bold" style={{ borderColor: agentColor(group.aggregates[0]), color: agentColor(group.aggregates[0]) }} aria-hidden="true">
                {group.aggregates[0].marker.slice(0, 1)}
              </span>
              <span className="flex flex-col">
                <strong>{primaryAgentName(group.aggregates[0].agent)}</strong>
                <small className="text-muted-foreground">{agentDetails(group.aggregates[0].agent) || group.aggregates[0].corpus}</small>
              </span>
            </div>
            <ul className="divide-y">
              {group.aggregates.map((aggregate) => (
                <li className="grid grid-cols-2 gap-3 p-4 xs:grid-cols-4" key={aggregate.id}>
                  <Badge variant="default">{aggregate.effort ?? "default"}</Badge>
                  <span className="flex flex-col"><strong className="font-mono text-sm">{aggregate.passedTasks.mean.toFixed(1)}/{aggregate.taskCount}</strong><small className="text-muted-foreground">tasks</small></span>
                  <span className="flex flex-col"><strong className="font-mono text-sm">{aggregate.agentSecondsPerTask.mean.toFixed(1)}s</strong><small className="text-muted-foreground">per task</small></span>
                  <Badge variant={aggregate.trialCount > 1 ? "pass" : "muted"}>
                    {evidenceLabel(aggregate)}
                  </Badge>
                  <small className="col-span-2 text-muted-foreground xs:col-span-4">
                    {aggregate.trialCount > 1 ? `95% CI ${formatInterval(aggregate)}` : `Observed ${aggregate.passedTasks.min.toFixed(0)} tasks`}
                    {` · ${aggregate.totalTimeouts} timeouts`}
                  </small>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>
    </>
  );
}

function SortButton({
  label,
  sortKey,
  sort,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  sort: SortState;
  onSort: (key: SortKey) => void;
}) {
  const isActive = sort.key === sortKey;
  return (
    <Button
      variant="ghost"
      size="sm"
      type="button"
      className="-ml-3 text-muted-foreground data-[active=true]:text-foreground"
      aria-label={`Sort by ${label}, ${isActive ? sort.direction : "unsorted"}`}
      data-active={isActive || undefined}
      onClick={() => onSort(sortKey)}
    >
      <span>{label}</span>
      <ArrowUpDown data-icon="inline-end" aria-hidden="true" />
    </Button>
  );
}

function sortAggregates(aggregates: LeaderboardAggregate[], sort: SortState) {
  return [...aggregates].sort((a, b) => {
    const direction = sort.direction === "asc" ? 1 : -1;
    const primary = compareAggregates(a, b, sort.key);
    if (primary !== 0) return primary * direction;
    if (sort.key === "tasksPassed") {
      return compareAggregates(a, b, "secondsPerTask");
    }
    return compareAggregates(a, b, "configuration") || compareAggregates(a, b, "effort");
  });
}

function compareAggregates(a: LeaderboardAggregate, b: LeaderboardAggregate, key: SortKey) {
  switch (key) {
    case "configuration":
      return a.agent.localeCompare(b.agent);
    case "effort":
      return effortValue(a) - effortValue(b);
    case "trialCount":
      return a.trialCount - b.trialCount;
    case "tasksPassed":
      return a.passedTasks.mean - b.passedTasks.mean;
    case "secondsPerTask":
      return a.agentSecondsPerTask.mean - b.agentSecondsPerTask.mean;
    case "timeouts":
      return a.totalTimeouts - b.totalTimeouts;
  }
}

function effortValue(aggregate: LeaderboardAggregate) {
  return aggregate.effort ? effortRank[aggregate.effort] : -1;
}

function groupAggregatesByModel(aggregates: LeaderboardAggregate[]) {
  const groups = new Map<string, LeaderboardAggregate[]>();
  for (const aggregate of aggregates) {
    const key = aggregate.series ?? aggregate.agent;
    const group = groups.get(key) ?? [];
    group.push(aggregate);
    groups.set(key, group);
  }

  return [...groups.entries()]
    .map(([key, entries]) => ({
      key,
      aggregates: entries.sort((left, right) => effortValue(left) - effortValue(right)),
    }))
    .sort((left, right) => primaryAgentName(left.aggregates[0].agent).localeCompare(primaryAgentName(right.aggregates[0].agent)));
}

function evidenceLabel(aggregate: LeaderboardAggregate) {
  if (aggregate.provenance === "composite") return "legacy composite";
  return aggregate.trialCount > 1 ? `${aggregate.trialCount} runs` : "single run";
}

function primaryAgentName(agent: string) {
  return agent.split(" via ")[0];
}

function agentDetails(agent: string) {
  const [, details] = agent.split(" via ", 2);
  return details ? `via ${details}` : "";
}

function agentColor(aggregate: LeaderboardAggregate) {
  return aggregate.series ? modelColors[aggregate.series] : "var(--muted-foreground)";
}

function formatInterval(aggregate: LeaderboardAggregate) {
  const low = aggregate.passedTasks.ci95Low;
  const high = aggregate.passedTasks.ci95High;
  return low == null || high == null ? "unavailable" : `${low.toFixed(1)}–${high.toFixed(1)}`;
}
