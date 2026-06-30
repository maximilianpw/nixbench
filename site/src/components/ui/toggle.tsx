import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const toggleVariants = cva("segmented-item", {
  variants: {
    variant: {
      default: "",
      outline: "segmented-item-outline",
    },
    size: {
      default: "",
      sm: "segmented-item-sm",
      lg: "segmented-item-lg",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});

export interface ToggleProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof toggleVariants> {
  pressed?: boolean;
}

function Toggle({ className, variant, size, pressed, ...props }: ToggleProps) {
  return (
    <button
      data-slot="toggle"
      aria-pressed={pressed}
      className={cn(toggleVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Toggle, toggleVariants };
