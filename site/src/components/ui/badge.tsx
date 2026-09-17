import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center rounded-sm border px-2 py-1 font-mono text-[0.68rem] font-semibold uppercase tracking-wider",
  {
    variants: {
      variant: {
        default: "border-primary bg-primary text-primary-foreground",
        pass: "border-pass/30 bg-pass/10 text-pass",
        fail: "border-fail/30 bg-fail/10 text-fail",
        codex: "border-codex/30 bg-codex/10 text-codex",
        claude: "border-claude/30 bg-claude/10 text-claude",
        muted: "border-border bg-muted text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant, className }))} {...props} />;
}

export { Badge, badgeVariants };
