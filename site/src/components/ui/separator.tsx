import * as React from "react";

import { cn } from "@/lib/utils";

export type SeparatorProps = React.HTMLAttributes<HTMLDivElement> & {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
};

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = "horizontal", decorative = true, ...props }, ref) => (
    <div
      data-slot="separator"
      ref={ref}
      className={cn("separator", orientation === "vertical" && "separator-vertical", className)}
      role={decorative ? "none" : "separator"}
      aria-orientation={decorative ? undefined : orientation}
      {...props}
    />
  ),
);
Separator.displayName = "Separator";

export { Separator };
