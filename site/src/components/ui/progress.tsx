import * as React from "react";

import { cn } from "@/lib/utils";

export type ProgressProps = React.HTMLAttributes<HTMLDivElement> & { value: number; max?: number };

function Progress({ className, value, max = 100, ...props }: ProgressProps) {
  const clampedValue = Math.max(0, Math.min(value, max));
  const percent = max === 0 ? 0 : (clampedValue / max) * 100;

  return (
    <div
      data-slot="progress"
      className={cn("relative h-2 w-full overflow-hidden rounded-full bg-muted", className)}
      role="progressbar"
      aria-valuemax={max}
      aria-valuemin={0}
      aria-valuenow={clampedValue}
      {...props}
    >
      <div className="h-full bg-nix-blue transition-transform" style={{ transform: `translateX(-${100 - percent}%)` }} />
    </div>
  );
}

export { Progress };
