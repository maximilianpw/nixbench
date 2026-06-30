import { LeaderboardPanel } from "@/components/charts/LeaderboardPanel";
import { ExplainerSection } from "@/components/pages/home/ExplainerSection";
import { HomeHero } from "@/components/pages/home/HomeHero";
import { MethodSection } from "@/components/pages/home/MethodSection";
import { TasksSection } from "@/components/pages/home/TasksSection";
import { UpdatesSection } from "@/components/pages/home/UpdatesSection";

export type HomePageProps = {};

export function HomePage({}: HomePageProps = {}) {
  return (
    <main className="app-page home-page">
      <HomeHero />
      <LeaderboardPanel />
      <ExplainerSection />
      <TasksSection />
      <MethodSection />
      <UpdatesSection />
    </main>
  );
}
