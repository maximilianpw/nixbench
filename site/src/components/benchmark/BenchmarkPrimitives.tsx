import type { ReactNode } from "react";
import { ArrowRight } from "lucide-react";

import { Badge, type BadgeProps } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

type SectionAction = {
  href: string;
  label: string;
};

type PageSectionProps = {
  id?: string;
  labelledBy?: string;
  className?: string;
  children: ReactNode;
};

export function PageSection({ id, labelledBy, className, children }: PageSectionProps) {
  return (
    <section id={id} className={cn("section", className)} aria-labelledby={labelledBy}>
      {children}
    </section>
  );
}

type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
  action?: SectionAction;
  headingId?: string;
  compact?: boolean;
};

export function SectionHeader({ eyebrow, title, description, action, headingId, compact }: SectionHeaderProps) {
  return (
    <div className={cn("section-heading", compact && "compact")}>
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2 id={headingId}>{title}</h2>
        {description ? <p className="section-description">{description}</p> : null}
      </div>
      {action ? (
        <Button asChild variant="ghost" size="sm">
          <a href={action.href}>
            {action.label}
            <ArrowRight data-icon="inline-end" aria-hidden="true" />
          </a>
        </Button>
      ) : null}
    </div>
  );
}

type StatGridProps = {
  items: readonly (readonly [string, string])[];
  label: string;
  className?: string;
};

export function StatGrid({ items, label, className }: StatGridProps) {
  return (
    <dl className={cn("stat-grid", className)} aria-label={label}>
      {items.map(([labelText, value]) => (
        <div key={labelText}>
          <dt>{labelText}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

type InsightCardProps = {
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

type MetricListProps = {
  metrics: readonly (readonly [string, string])[];
};

export function MetricList({ metrics }: MetricListProps) {
  return (
    <dl className="metric-list">
      {metrics.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

type ScoreCardProps = {
  title: string;
  eyebrow: string;
  value: string;
  max?: string;
  description?: string;
  badgeVariant?: BadgeProps["variant"];
  metrics?: readonly (readonly [string, string])[];
};

export function ScoreCard({
  title,
  eyebrow,
  value,
  max,
  description,
  badgeVariant = "default",
  metrics,
}: ScoreCardProps) {
  const numericValue = Number(value);
  const numericMax = Number(max);

  return (
    <Card className="score-card">
      <CardHeader>
        <Badge variant={badgeVariant}>{eyebrow}</Badge>
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

type MethodStepProps = {
  label: string;
  description: string;
};

export function MethodStep({ label, description }: MethodStepProps) {
  return (
    <li>
      <Badge variant="default">{label}</Badge>
      <p>{description}</p>
    </li>
  );
}

export function InlineSeparator() {
  return <Separator className="inline-separator" />;
}
