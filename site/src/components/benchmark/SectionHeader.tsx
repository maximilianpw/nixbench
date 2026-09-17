import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type SectionHeaderAction = { href: string; label: string };
export type SectionHeaderProps = { title: string; description?: string; action?: SectionHeaderAction; headingId?: string; compact?: boolean };

export function SectionHeader({ title, description, action, headingId, compact }: SectionHeaderProps) {
  return (
    <div className={cn("mb-10 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between", compact && "mb-6")}>
      <div className="max-w-3xl">
        <h2 id={headingId} className={cn("text-3xl font-semibold tracking-tight sm:text-4xl", compact && "text-2xl sm:text-3xl")}>{title}</h2>
        {description ? <p className="mt-3 max-w-2xl text-base leading-7 text-muted-foreground">{description}</p> : null}
      </div>
      {action ? (
        <Button asChild variant="ghost" size="sm">
          <a href={action.href}>{action.label}<ArrowRight aria-hidden="true" /></a>
        </Button>
      ) : null}
    </div>
  );
}
