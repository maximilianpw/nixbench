import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export type PageSectionProps = {
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
