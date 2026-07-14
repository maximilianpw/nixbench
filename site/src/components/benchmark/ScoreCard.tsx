import { MetricList } from "@/components/benchmark/MetricList";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export type ScoreCardProps = {
  title: string;
  value: string;
  max?: string;
  description?: string;
  metrics?: readonly (readonly [string, string])[];
};

export function ScoreCard({
  title,
  value,
  max,
  description,
  metrics,
}: ScoreCardProps) {
  const numericValue = Number(value);
  const numericMax = Number(max);

  return (
    <Card className="score-card">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent>
        <p className="score-value">
          {value}
          {max ? <span>/{max}</span> : null}
        </p>
        {Number.isFinite(numericValue) && Number.isFinite(numericMax) ? (
          <Progress value={numericValue} max={numericMax} aria-label={`${title} score`} />
        ) : null}
      </CardContent>
      {metrics ? (
        <CardFooter>
          <MetricList metrics={metrics} />
        </CardFooter>
      ) : null}
    </Card>
  );
}
