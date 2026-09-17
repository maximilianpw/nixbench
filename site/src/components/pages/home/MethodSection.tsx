import { MethodStep } from "@/components/benchmark/MethodStep";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { methodSteps } from "@/data/benchmark";

export type MethodSectionProps = {};

export function MethodSection({}: MethodSectionProps = {}) {
  return (
    <section className="method-band" aria-labelledby="method-heading">
      <div className="section method-section">
        <SectionHeader
          title="How NixBench works"
          description="One repeatable process separates the agent from the evaluator."
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
