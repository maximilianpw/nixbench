import { MethodStep } from "@/components/benchmark/MethodStep";
import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { methodSteps } from "@/data/benchmark";

export type MethodSectionProps = {};

export function MethodSection({}: MethodSectionProps = {}) {
  return (
    <PageSection className="method-section" labelledBy="method-heading">
      <SectionHeader
        eyebrow="Methodology"
        title="The agent edits a worktree. The evaluator scores the result."
        headingId="method-heading"
        action={{ href: "docs/running-agents.html", label: "Run guide" }}
      />
      <ol className="method-list">
        {methodSteps.map(([label, description]) => (
          <MethodStep key={label} label={label} description={description} />
        ))}
      </ol>
    </PageSection>
  );
}
