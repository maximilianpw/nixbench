import { useMemo, useState } from "react";
import { ArrowUpDown } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { LeaderboardRun } from "@/data/benchmark";

export type LeaderboardTableProps = {
  runs: LeaderboardRun[];
};

type SortKey = "run" | "effort" | "passRate" | "score" | "agentTimeSeconds" | "failed";
type SortDirection = "asc" | "desc";
type SortState = {
  key: SortKey;
  direction: SortDirection;
};

const defaultSort: SortState = { key: "passRate", direction: "desc" };
const effortRank = {
  low: 0,
  medium: 1,
  high: 2,
  xhigh: 3,
  max: 4,
  ultra: 5,
} as const;

export function LeaderboardTable({ runs }: LeaderboardTableProps) {
  const [sort, setSort] = useState<SortState>(defaultSort);
  const sortedRuns = useMemo(() => sortRuns(runs, sort), [runs, sort]);

  const toggleSort = (key: SortKey) => {
    setSort((current) => ({
      key,
      direction: current.key === key && current.direction === "desc" ? "asc" : "desc",
    }));
  };

  const ariaSortFor = (key: SortKey) => {
    if (sort.key !== key) {
      return undefined;
    }

    return sort.direction === "asc" ? "ascending" : "descending";
  };

  return (
    <Table
      className="leaderboard-table"
      containerClassName="leaderboard-table-wrap"
      aria-label="NixBench run leaderboard"
    >
      <TableHeader>
        <TableRow>
          <TableHead scope="col" aria-sort={ariaSortFor("run")}>
            <SortButton label="Run" sortKey="run" sort={sort} onSort={toggleSort} />
          </TableHead>
          <TableHead scope="col" aria-sort={ariaSortFor("effort")}>
            <SortButton label="Effort" sortKey="effort" sort={sort} onSort={toggleSort} />
          </TableHead>
          <TableHead scope="col" aria-sort={ariaSortFor("passRate")}>
            <SortButton label="Pass@1" sortKey="passRate" sort={sort} onSort={toggleSort} />
          </TableHead>
          <TableHead scope="col" aria-sort={ariaSortFor("score")}>
            <SortButton label="Score" sortKey="score" sort={sort} onSort={toggleSort} />
          </TableHead>
          <TableHead scope="col" aria-sort={ariaSortFor("agentTimeSeconds")}>
            <SortButton label="Agent time" sortKey="agentTimeSeconds" sort={sort} onSort={toggleSort} />
          </TableHead>
          <TableHead scope="col" aria-sort={ariaSortFor("failed")}>
            <SortButton label="Failed" sortKey="failed" sort={sort} onSort={toggleSort} />
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sortedRuns.map((run) => (
          <TableRow key={run.id}>
            <TableHead scope="row">
              <span className="agent-cell">
                <span className={`agent-mark ${run.kind}`} aria-hidden="true">
                  {run.marker}
                </span>
                <span>
                  <strong>{run.agent}</strong>
                  <small>
                    {run.corpus} · {run.runId}
                  </small>
                </span>
              </span>
            </TableHead>
            <TableCell>
              <Badge variant="default">{run.effort ?? "default"}</Badge>
            </TableCell>
            <TableCell>
              <span className="score-percent">{run.passRate}%</span>
              <Progress value={run.passRate} aria-label={`${run.agent} pass rate`} />
            </TableCell>
            <TableCell>
              {run.score} / {run.maxScore}
            </TableCell>
            <TableCell>{run.agentTimeLabel}</TableCell>
            <TableCell>
              {run.failed}
              <small className="task-count-note">
                {run.completedTasks}/{run.totalTasks}
              </small>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
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
  const directionLabel = isActive ? sort.direction : "unsorted";

  return (
    <Button
      variant="ghost"
      size="sm"
      type="button"
      className="table-sort"
      aria-label={`Sort by ${label}, ${directionLabel}`}
      data-active={isActive || undefined}
      onClick={() => onSort(sortKey)}
    >
      <span>{label}</span>
      <ArrowUpDown data-icon="inline-end" aria-hidden="true" />
    </Button>
  );
}

function sortRuns(runs: LeaderboardRun[], sort: SortState) {
  return [...runs].sort((a, b) => {
    const direction = sort.direction === "asc" ? 1 : -1;
    const primary = compareRuns(a, b, sort.key);

    if (primary !== 0) {
      return primary * direction;
    }

    return compareRuns(a, b, "run") || compareRuns(a, b, "effort");
  });
}

function compareRuns(a: LeaderboardRun, b: LeaderboardRun, key: SortKey) {
  switch (key) {
    case "run":
      return `${a.agent} ${a.runId}`.localeCompare(`${b.agent} ${b.runId}`);
    case "effort":
      return effortValue(a) - effortValue(b);
    case "passRate":
      return a.passRate - b.passRate;
    case "score":
      return a.score - b.score;
    case "agentTimeSeconds":
      return a.agentTimeSeconds - b.agentTimeSeconds;
    case "failed":
      return a.failed - b.failed;
  }
}

function effortValue(run: LeaderboardRun) {
  return run.effort ? effortRank[run.effort] : -1;
}
