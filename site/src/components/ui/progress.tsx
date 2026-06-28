import * as React from "react";

import { cn } from "@/lib/utils";

type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
  value: number;
  max?: number;
};

function Progress({ className, value, max = 100, ...props }: ProgressProps) {
  const clampedValue = Math.max(0, Math.min(value, max));
  const percent = max === 0 ? 0 : (clampedValue / max) * 100;

  return (
    <div
      className={cn("progress", className)}
      role="progressbar"
      aria-valuemax={max}
      aria-valuemin={0}
      aria-valuenow={clampedValue}
      {...props}
    >
      <div
        className="progress-indicator"
        style={{ "--progress-value": `${percent}%` } as React.CSSProperties}
      />
    </div>
  );
}

export { Progress };
