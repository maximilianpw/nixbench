import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export type InsightCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  variant?: BadgeProps["variant"];
};

export function InsightCard({ eyebrow, title, description, variant = "muted" }: InsightCardProps) {
  return (
    <Card className="insight-card">
      <CardHeader>
        <Badge variant={variant}>{eyebrow}</Badge>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <CardDescription>{description}</CardDescription>
      </CardContent>
    </Card>
  );
}
