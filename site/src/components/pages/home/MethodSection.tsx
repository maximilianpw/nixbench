import { MethodStep } from "@/components/benchmark/MethodStep";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { methodSteps } from "@/data/benchmark";

export function MethodSection() {
  return (
    <section className="border-y bg-card" aria-labelledby="method-heading">
      <div className="section-shell">
        <SectionHeader title="How NixBench works" description="One repeatable process separates the agent from the evaluator." headingId="method-heading" action={{ href: "docs/running-agents.html", label: "Read the protocol" }} />
        <ol className="grid gap-6 lg:grid-cols-3">
          {methodSteps.map(([label, description]) => <MethodStep key={label} label={label} description={description} />)}
        </ol>
      </div>
    </section>
  );
}
