import { MetricList } from "@/components/benchmark/MetricList";
import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { modelSummaries, passedTasks } from "@/data/benchmark";

export type ResultsSummaryProps = {};

export function ResultsSummary({}: ResultsSummaryProps = {}) {
  return (
    <PageSection className="results-summary" labelledBy="summary-heading">
      <SectionHeader
        eyebrow="Model families"
        title="Best rows by model, with every scored run preserved below."
        description="Each card groups the runs for one model family, so the summary expands with the dataset instead of assuming a fixed set of models."
        headingId="summary-heading"
        action={{ href: "docs/runs/2026-06-24-model-comparison.html", label: "Source notes" }}
      />

      <div className="model-summary-grid" aria-label="Model family summaries">
        {modelSummaries.map((summary) => {
          const passRate = summary.bestRun ? (passedTasks(summary.bestRun) / summary.bestRun.totalTasks) * 100 : 0;
          const badgeVariant = (summary.kind ?? "muted") as BadgeProps["variant"];

          return (
            <Card key={summary.key} className="model-summary-card">
              <CardHeader>
                <div className="model-card-topline">
                  <Badge variant={badgeVariant}>{summary.kind ?? "pending"}</Badge>
                  <span>{summary.runCount} runs</span>
                </div>
                <CardTitle>{summary.label}</CardTitle>
                <CardDescription>
                  Best effort: {summary.bestEffortLabel}
                  {summary.bestRun ? ` · ${summary.bestRun.runId}` : ""}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="model-score-row">
                  <div>
                    <span>{summary.bestPassLabel}</span>
                    <small>best pass count</small>
                  </div>
                  <strong>{summary.bestScoreLabel}</strong>
                </div>
                <Progress value={passRate} aria-label={`${summary.label} best pass rate`} />
                <MetricList
                  metrics={[
                    ["Efforts", summary.effortLabel],
                    ["Fastest row", summary.fastestRunLabel],
                    ["Timeouts", summary.timeoutLabel],
                    ["Best score", summary.bestScoreLabel],
                  ]}
                />
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="result-note-grid" aria-label="Comparison notes">
        <Card className="result-note-card">
          <CardHeader>
            <Badge variant="default">Scope</Badge>
            <CardTitle>Rows are runs, cards are models.</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              The leaderboard keeps every effort-level row visible while this section compresses each model family to
              its best observed row.
            </CardDescription>
          </CardContent>
        </Card>
        <Card className="result-note-card">
          <CardHeader>
            <Badge variant="default">Corpus</Badge>
            <CardTitle>Denominators stay attached.</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Historical rows cover 26 tasks; current GPT-5.6 rows cover 29. Compare pass rates or filter to one corpus
              before comparing raw pass counts.
            </CardDescription>
          </CardContent>
        </Card>
        <Card className="result-note-card">
          <CardHeader>
            <Badge variant="default">Evidence</Badge>
            <CardTitle>Observed runs, not confidence intervals.</CardTitle>
          </CardHeader>
          <CardContent>
            <CardDescription>
              Each row records one completed run. The table shows what happened in that run rather than claiming a
              statistically stable model ranking.
            </CardDescription>
          </CardContent>
        </Card>
      </div>
    </PageSection>
  );
}
