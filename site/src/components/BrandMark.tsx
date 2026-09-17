import { cn } from "@/lib/utils";

export type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className }: BrandMarkProps) {
  return (
    <svg className={cn("size-7 shrink-0", className)} viewBox="0 0 40 40" aria-hidden="true">
      <rect className="fill-foreground" x="1" y="1" width="38" height="38" rx="5" />
      <path className="fill-background" d="M9 29V11h5.2l11.6 12.3V11H31v18h-5.1L14.2 16.5V29H9Z" />
      <path className="fill-nix-blue" d="M9 7h13v2H9z" />
    </svg>
  );
}
