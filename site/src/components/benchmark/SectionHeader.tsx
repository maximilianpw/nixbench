import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type SectionHeaderAction = {
  href: string;
  label: string;
};

export type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
  action?: SectionHeaderAction;
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
