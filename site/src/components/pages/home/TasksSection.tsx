import { PageSection } from "@/components/benchmark/PageSection";
import { SectionHeader } from "@/components/benchmark/SectionHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { currentCorpusTaskCount, difficultyDistribution, taskExamples } from "@/data/benchmark";

export type TasksSectionProps = {};

export function TasksSection({}: TasksSectionProps = {}) {
  return (
    <PageSection id="tasks" className="tasks-section" labelledBy="tasks-heading">
      <SectionHeader
        eyebrow="Task examples"
        title={`${currentCorpusTaskCount} small repositories, one hidden evaluator each.`}
        headingId="tasks-heading"
        action={{
          href: "https://github.com/maximilianpw/nixbench#what-it-measures",
          label: `All ${currentCorpusTaskCount} tasks`,
        }}
      />

      <div className="task-grid">
        {taskExamples.map((task) => (
          <Card key={task.title} className="task-card">
            <CardHeader>
              <Badge variant="default">{task.area}</Badge>
              <CardTitle>{task.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{task.description}</CardDescription>
            </CardContent>
            <CardFooter>
              <span>difficulty</span>
              <strong>{task.difficulty}</strong>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="difficulty-strip">
        {difficultyDistribution.map(([count, description]) => (
          <Card key={count} className="distribution-card">
            <CardHeader>
              <CardTitle>{count}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription>{description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </PageSection>
  );
}
