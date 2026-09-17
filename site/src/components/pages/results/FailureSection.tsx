import { InsightCard } from "@/components/benchmark/InsightCard";
import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { failureNotes } from "@/data/benchmark";

export function FailureSection() {
  return (
    <PageSection labelledBy="failure-heading">
      <SectionHeader title="Several outcome patterns repeat across runs." headingId="failure-heading" />
      <div className="grid gap-4 md:grid-cols-3">{failureNotes.map((note) => <InsightCard key={note.title} title={note.title} description={note.description} />)}</div>
    </PageSection>
  );
}
