import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { modelSummaries } from "@/data/benchmark";

export type ResultsSummaryProps = {};

export function ResultsSummary({}: ResultsSummaryProps = {}) {
  return (
    <PageSection className="results-summary" labelledBy="summary-heading">
      <SectionHeader
        eyebrow="Model index"
        title="One comparable summary row per model family."
        description="Best observed pass rate is shown with its corpus and effort; every underlying comparison row remains available in the leaderboard."
        headingId="summary-heading"
        action={{ href: "docs/runs/2026-06-24-model-comparison.html", label: "Source notes" }}
      />

      <Table
        className="model-index-table"
        containerClassName="model-index-table-wrap"
        aria-label="Model family benchmark summary"
      >
        <TableHeader>
          <TableRow>
            <TableHead scope="col">Model</TableHead>
            <TableHead scope="col">Best observed</TableHead>
            <TableHead scope="col">Corpus</TableHead>
            <TableHead scope="col">Effort</TableHead>
            <TableHead scope="col">Fastest row</TableHead>
            <TableHead scope="col">Coverage</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {modelSummaries.map((summary) => {
            const badgeVariant = (summary.kind ?? "muted") as BadgeProps["variant"];

            return (
              <TableRow key={summary.key}>
                <TableHead scope="row">
                  <span className="model-index-name">
                    <Badge variant={badgeVariant}>{summary.kind ?? "pending"}</Badge>
                    <strong>{summary.label}</strong>
                  </span>
                </TableHead>
                <TableCell>
                  <span className="model-index-score">
                    <strong>{summary.bestPassLabel}</strong>
                    <Progress
                      value={summary.bestRun?.passRate ?? 0}
                      aria-label={`${summary.label} best observed pass rate`}
                    />
                    <small>{summary.bestScoreLabel}</small>
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant="muted">{summary.bestRun?.corpus ?? "--"}</Badge>
                </TableCell>
                <TableCell>{summary.bestEffortLabel}</TableCell>
                <TableCell>{summary.fastestRunLabel}</TableCell>
                <TableCell>
                  <span className="model-index-coverage">
                    <strong>{summary.runCount}</strong> rows
                    <small>{summary.timeoutLabel} timeouts</small>
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <aside className="publication-notes" aria-label="How to read these results">
        <p>
          <strong>Corpus-aware.</strong> Historical 26-task and current 29-task rows retain separate denominators.
        </p>
        <p>
          <strong>Row-level evidence.</strong> Each value is a completed run or documented composite, not a confidence interval.
        </p>
        <p>
          <strong>Effort is explicit.</strong> “Best” identifies the strongest observed row, not a default model setting.
        </p>
      </aside>
    </PageSection>
  );
}
