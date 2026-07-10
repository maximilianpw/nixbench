import { Badge } from "@/components/ui/badge";

export type MethodStepProps = {
  label: string;
  description: string;
};

export function MethodStep({ label, description }: MethodStepProps) {
  return (
    <li>
      <Badge variant="default">{label}</Badge>
      <p>{description}</p>
    </li>
  );
}
