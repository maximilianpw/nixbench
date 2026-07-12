import { type CSSProperties, useMemo, useState } from "react";
import { ArrowUpDown } from "lucide-react";

import { modelColors } from "@/components/charts/model-colors";
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
  const rankById = useMemo(() => buildRanks(runs), [runs]);

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
    <>
      <Table
        className="leaderboard-table"
        containerClassName="leaderboard-table-wrap"
        aria-label="NixBench comparison leaderboard"
      >
        <TableHeader>
          <TableRow>
            <TableHead scope="col" className="rank-column">Rank</TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("run")}>
              <SortButton label="Run" sortKey="run" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("effort")}>
              <SortButton label="Effort" sortKey="effort" sort={sort} onSort={toggleSort} />
            </TableHead>
            <TableHead scope="col" aria-sort={ariaSortFor("passRate")}>
              <SortButton label="Pass rate" sortKey="passRate" sort={sort} onSort={toggleSort} />
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
              <TableCell className="rank-cell">#{rankById.get(run.id)}</TableCell>
              <TableHead scope="row">
                <span className="agent-cell">
                  <span className={`agent-mark ${run.kind}`} style={agentMarkStyle(run)} aria-hidden="true">
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

      <ol className="leaderboard-mobile-list" aria-label="NixBench comparison leaderboard">
        {sortedRuns.map((run) => (
          <li key={run.id}>
            <div className="mobile-rank">#{rankById.get(run.id)}</div>
            <div className="mobile-run-heading">
              <span className={`agent-mark ${run.kind}`} style={agentMarkStyle(run)} aria-hidden="true">
                {run.marker}
              </span>
              <span>
                <strong>{run.agent}</strong>
                <small>{run.corpus}</small>
              </span>
              <Badge variant="default">{run.effort ?? "default"}</Badge>
            </div>
            <dl>
              <div>
                <dt>Pass rate</dt>
                <dd>{run.passRate}%</dd>
              </div>
              <div>
                <dt>Score</dt>
                <dd>{run.score}/{run.maxScore}</dd>
              </div>
              <div>
                <dt>Agent time</dt>
                <dd>{run.agentTimeLabel}</dd>
              </div>
              <div>
                <dt>Failed</dt>
                <dd>{run.failed}</dd>
              </div>
            </dl>
            <small className="mobile-run-id">{run.runId}</small>
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

    if (sort.key === "passRate" || sort.key === "score") {
      const efficiencyTieBreak = compareRuns(a, b, "agentTimeSeconds");
      if (efficiencyTieBreak !== 0) {
        return efficiencyTieBreak;
      }
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
      return a.score / a.maxScore - b.score / b.maxScore;
    case "agentTimeSeconds":
      return a.agentTimeSeconds - b.agentTimeSeconds;
    case "failed":
      return a.failed / a.totalTasks - b.failed / b.totalTasks;
  }
}

function effortValue(run: LeaderboardRun) {
  return run.effort ? effortRank[run.effort] : -1;
}

function agentMarkStyle(run: LeaderboardRun) {
  return run.series ? ({ "--agent-color": modelColors[run.series] } as CSSProperties) : undefined;
}

function buildRanks(runs: LeaderboardRun[]) {
  return new Map(
    [...runs]
      .sort(
        (a, b) =>
          b.passRate - a.passRate ||
          a.agentTimeSeconds - b.agentTimeSeconds ||
          a.agent.localeCompare(b.agent),
      )
      .map((run, index) => [run.id, index + 1]),
  );
}
