import { type CSSProperties, useMemo, useState } from "react";
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

const defaultSort: SortState = { key: "tasksPassed", direction: "desc" };
const effortRank = { low: 0, medium: 1, high: 2, xhigh: 3, max: 4, ultra: 5 } as const;

export function LeaderboardTable({
  aggregates,
  highlightedModel,
  onHighlightedModelChange,
}: LeaderboardTableProps) {
  const [sort, setSort] = useState<SortState>(defaultSort);
  const sortedAggregates = useMemo(() => sortAggregates(aggregates, sort), [aggregates, sort]);

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
        className="leaderboard-table evidence-table"
        containerClassName="leaderboard-table-wrap"
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
              style={agentMarkStyle(aggregate)}
              onPointerEnter={() => onHighlightedModelChange(aggregate.series ?? null)}
            >
              <TableHead scope="row">
                <span className="agent-cell">
                  <span className={`agent-mark ${aggregate.kind}`} style={agentMarkStyle(aggregate)} aria-hidden="true">
                    {aggregate.marker}
                  </span>
                  <span>
                    <strong>{aggregate.agent}</strong>
                    <small>{aggregate.corpus} · {aggregate.trialCount} recorded {aggregate.trialCount === 1 ? "trial" : "trials"}</small>
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
                <span className="score-percent">{aggregate.passedTasks.mean.toFixed(1)} / {aggregate.taskCount}</span>
                <Progress
                  value={(aggregate.passedTasks.mean / aggregate.taskCount) * 100}
                  aria-label={`${aggregate.agent} ${aggregate.effort ?? "default"} mean tasks passed`}
                />
              </TableCell>
              <TableCell>
                <span className="interval-cell">
                  <strong>{formatInterval(aggregate)}</strong>
                  <small>observed {aggregate.passedTasks.min.toFixed(0)}–{aggregate.passedTasks.max.toFixed(0)}</small>
                </span>
              </TableCell>
              <TableCell>
                <span className="interval-cell">
                  <strong>{aggregate.agentSecondsPerTask.mean.toFixed(1)}s</strong>
                  <small>{formatDuration(aggregate.agentTimeSeconds.mean)} / corpus</small>
                </span>
              </TableCell>
              <TableCell>{aggregate.totalTimeouts}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <ol className="leaderboard-mobile-list evidence-mobile-list" aria-label="NixBench configuration evidence">
        {sortedAggregates.map((aggregate) => (
          <li key={aggregate.id}>
            <div className="mobile-run-heading">
              <span className={`agent-mark ${aggregate.kind}`} style={agentMarkStyle(aggregate)} aria-hidden="true">
                {aggregate.marker}
              </span>
              <span>
                <strong>{aggregate.agent}</strong>
                <small>{aggregate.corpus}</small>
              </span>
              <Badge variant="default">{aggregate.effort ?? "default"}</Badge>
            </div>
            <dl>
              <div>
                <dt>Evidence</dt>
                <dd>{aggregate.provenance === "composite" ? "composite" : aggregate.trialCount === 1 ? "single run" : `n=${aggregate.trialCount}`}</dd>
              </div>
              <div><dt>Mean tasks</dt><dd>{aggregate.passedTasks.mean.toFixed(1)}/{aggregate.taskCount}</dd></div>
              <div><dt>95% CI</dt><dd>{formatInterval(aggregate)}</dd></div>
              <div><dt>Seconds / task</dt><dd>{aggregate.agentSecondsPerTask.mean.toFixed(1)}s</dd></div>
            </dl>
            <small className="mobile-run-id">Observed {aggregate.passedTasks.min.toFixed(0)}–{aggregate.passedTasks.max.toFixed(0)} tasks · {aggregate.totalTimeouts} timeouts</small>
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
      className="table-sort"
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

function agentMarkStyle(aggregate: LeaderboardAggregate) {
  return aggregate.series ? ({ "--agent-color": modelColors[aggregate.series] } as CSSProperties) : undefined;
}

function formatInterval(aggregate: LeaderboardAggregate) {
  const low = aggregate.passedTasks.ci95Low;
  const high = aggregate.passedTasks.ci95High;
  return low == null || high == null ? "unavailable" : `${low.toFixed(1)}–${high.toFixed(1)}`;
}
