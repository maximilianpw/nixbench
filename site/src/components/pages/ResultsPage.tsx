import { LeaderboardPanel } from "@/components/charts/LeaderboardPanel";
 import { FailureSection } from "@/components/pages/results/FailureSection";
 import { ResultsHero } from "@/components/pages/results/ResultsHero";
 import { ResultsSummary } from "@/components/pages/results/ResultsSummary";
 import { TaskResultsSection } from "@/components/pages/results/TaskResultsSection";
 import { TimingSection } from "@/components/pages/results/TimingSection";
 
 export type ResultsPageProps = {};
 
 export function ResultsPage({}: ResultsPageProps = {}) {
   return (
     <main className="app-page results-page">
      <ResultsHero />
      <LeaderboardPanel />
      <ResultsSummary />
       <TaskResultsSection />
       <TimingSection />
       <FailureSection />
     </main>
   );
}
