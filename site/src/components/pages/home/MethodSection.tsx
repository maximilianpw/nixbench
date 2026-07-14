import { MethodStep } from "@/components/benchmark/MethodStep";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { methodSteps } from "@/data/benchmark";

export type MethodSectionProps = {};

export function MethodSection({}: MethodSectionProps = {}) {
  return (
    <section className="method-band" aria-labelledby="method-heading">
      <div className="section method-section">
        <SectionHeader
          title="The agent edits a worktree. The evaluator scores the result."
          description="A simple, inspectable protocol separates generation from evaluation."
          headingId="method-heading"
          action={{ href: "docs/running-agents.html", label: "Read the protocol" }}
        />
        <ol className="method-list">
          {methodSteps.map(([label, description]) => (
            <MethodStep key={label} label={label} description={description} />
          ))}
        </ol>
      </div>
    </section>
  );
}
