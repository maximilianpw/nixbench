import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export type InsightCardProps = {
  title: string;
  description: string;
};

export function InsightCard({ title, description }: InsightCardProps) {
  return (
    <Card className="insight-card">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  );
}
