import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { modelSummaries } from "@/data/benchmark";

export function ResultsSummary() {
  return (
    <PageSection labelledBy="summary-heading">
      <SectionHeader title="Coverage by model family, without picking a lucky winner." description="Ranges summarize configuration means. Trial and replication counts show how much evidence sits behind each family." headingId="summary-heading" action={{ href: "docs/reproducibility.html", label: "Methodology" }} />
      <Table aria-label="Model family evidence coverage">
        <TableHeader><TableRow><TableHead scope="col">Model</TableHead><TableHead scope="col">Corpus</TableHead><TableHead scope="col">Mean task range</TableHead><TableHead scope="col">Seconds / task range</TableHead><TableHead scope="col">Effort settings</TableHead><TableHead scope="col">Evidence</TableHead></TableRow></TableHeader>
        <TableBody>
          {modelSummaries.map((summary) => {
            const badgeVariant: BadgeProps["variant"] = summary.kind === "codex" ? "codex" : summary.kind === "claude" ? "claude" : "muted";
            return (
              <TableRow key={summary.key}>
                <TableHead scope="row"><span className="flex items-center gap-2 normal-case tracking-normal"><Badge variant={badgeVariant}>{summary.kind ?? "pending"}</Badge><strong className="font-sans text-sm text-foreground">{summary.label}</strong></span></TableHead>
                <TableCell><Badge variant="muted">{summary.corpus}</Badge></TableCell>
                <TableCell><strong>{summary.taskRangeLabel}</strong> tasks</TableCell>
                <TableCell>{summary.secondsPerTaskRangeLabel}</TableCell>
                <TableCell>{summary.effortLabel}</TableCell>
                <TableCell><span className="flex flex-col"><strong>{summary.trialCount} trials · {summary.configurationCount} configurations</strong><small className="text-muted-foreground">{summary.replicatedConfigurationCount}/{summary.configurationCount} replicated · {summary.timeoutLabel} timeouts</small></span></TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <aside className="mt-6 grid gap-3 rounded-lg border bg-muted/40 p-5 text-sm leading-6 text-muted-foreground md:grid-cols-3" aria-label="How to read these results">
        <p><strong className="text-foreground">Corpus-separated.</strong> The 26- and 29-task datasets never share one plot or ranking.</p>
        <p><strong className="text-foreground">Trial-aware.</strong> Hollow points are single observations; filled means and confidence bars require replication.</p>
        <p><strong className="text-foreground">No winner selection.</strong> Every recorded effort configuration remains visible instead of reporting only its luckiest run.</p>
      </aside>
    </PageSection>
  );
}
