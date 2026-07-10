import { InsightCard } from "@/components/benchmark/InsightCard";
import { PageSection } from "@/components/benchmark/PageSection";
import { explainerCards } from "@/data/benchmark";

export type ExplainerSectionProps = {};

export function ExplainerSection({}: ExplainerSectionProps = {}) {
  return (
    <PageSection className="explainer-section" labelledBy="why-heading">
      <div className="narrative">
        <p className="eyebrow">Why this exists</p>
        <h2 id="why-heading">Plausible Nix often fails at evaluation time.</h2>
        <p>
          The benchmark gives agents a copied starter tree, a prompt, and no access to the hidden evaluator. It rewards
          final worktree behavior, not a fluent explanation of what the code should do.
        </p>
      </div>
      <div className="insight-grid">
        {explainerCards.map((card) => (
          <InsightCard key={card.title} eyebrow={card.kicker} title={card.title} description={card.description} />
        ))}
      </div>
    </PageSection>
  );
}
