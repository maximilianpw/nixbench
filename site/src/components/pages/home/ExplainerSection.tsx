import { InsightCard } from "@/components/benchmark/InsightCard";
import { PageSection } from "@/components/benchmark/PageSection";
import { explainerCards } from "@/data/benchmark";

export type ExplainerSectionProps = {};

export function ExplainerSection({}: ExplainerSectionProps = {}) {
  return (
    <PageSection className="explainer-section" labelledBy="why-heading">
      <div className="narrative">
        <h2 id="why-heading">Why trust the results?</h2>
        <p>
          Agents see the repository and task, but not the evaluator. Their final code must pass the same executable
          checks to earn a score.
        </p>
      </div>
      <div className="insight-grid">
        {explainerCards.map((card) => (
          <InsightCard key={card.title} title={card.title} description={card.description} />
        ))}
      </div>
    </PageSection>
  );
}
