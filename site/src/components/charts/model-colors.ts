import { resultColumns, type ModelKey } from "@/data/benchmark";

const modelColorPalette = [
  "var(--pass)",
  "var(--codex)",
  "var(--cyan)",
  "var(--claude)",
  "var(--amber)",
  "color-mix(in srgb, var(--nix-blue) 68%, var(--fail))",
  "color-mix(in srgb, var(--pass) 72%, var(--nix-blue))",
  "color-mix(in srgb, var(--claude) 72%, var(--fail))",
] as const;

export const modelColors = Object.fromEntries(
  resultColumns.map((column, index) => [column.key, modelColorPalette[index % modelColorPalette.length]]),
) as Record<ModelKey, string>;
