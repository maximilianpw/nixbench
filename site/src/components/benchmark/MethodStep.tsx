import { Badge } from "@/components/ui/badge";

export type MethodStepProps = { label: string; description: string };

export function MethodStep({ label, description }: MethodStepProps) {
  return (
    <li className="grid gap-3 border-t pt-6 sm:grid-cols-[8rem_1fr]">
      <Badge>{label}</Badge>
      <p className="leading-7 text-muted-foreground">{description}</p>
    </li>
  );
}
