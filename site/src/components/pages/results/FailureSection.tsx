import { InsightCard } from "@/components/benchmark/InsightCard";
import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { failureNotes } from "@/data/benchmark";

export type FailureSectionProps = {};

export function FailureSection({}: FailureSectionProps = {}) {
  return (
    <PageSection className="failure-section" labelledBy="failure-heading">
      <SectionHeader
        eyebrow="Outcome notes"
        title="Several outcome patterns repeat across runs."
        headingId="failure-heading"
      />
      <div className="insight-grid">
        {failureNotes.map((note) => (
          <InsightCard key={note.title} eyebrow={note.kicker} title={note.title} description={note.description} />
        ))}
      </div>
    </PageSection>
  );
}
