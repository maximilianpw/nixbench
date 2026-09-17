import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export type InsightCardProps = { title: string; description: string };

export function InsightCard({ title, description }: InsightCardProps) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent><p className="text-sm leading-6 text-muted-foreground">{description}</p></CardContent>
    </Card>
  );
}
