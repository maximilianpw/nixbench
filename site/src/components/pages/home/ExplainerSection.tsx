import { InsightCard } from "@/components/benchmark/InsightCard";
import { PageSection } from "@/components/benchmark/PageSection";
import { explainerCards } from "@/data/benchmark";

export function ExplainerSection() {
  return (
    <PageSection labelledBy="why-heading">
      <div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr]">
        <div className="max-w-xl">
          <h2 id="why-heading" className="text-3xl font-semibold tracking-tight sm:text-4xl">Why trust the results?</h2>
          <p className="mt-4 text-lg leading-8 text-muted-foreground">Agents see the repository and task, but not the evaluator. Their final code must pass the same executable checks to earn a score.</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {explainerCards.map((card) => <InsightCard key={card.title} title={card.title} description={card.description} />)}
        </div>
      </div>
    </PageSection>
  );
}
