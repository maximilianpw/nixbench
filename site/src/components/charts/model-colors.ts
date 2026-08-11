import type { ModelKey } from "@/data/benchmark";

export const modelColors = {
  gpt55: "var(--pass)",
  gpt54: "var(--codex)",
  gpt54Mini: "var(--cyan)",
  claudeOpus48: "var(--claude)",
  gpt56Sol: "var(--amber)",
  gpt56Terra: "color-mix(in srgb, var(--nix-blue) 68%, var(--fail))",
  gpt56Luna: "color-mix(in srgb, var(--pass) 72%, var(--nix-blue))",
  gemma4Local: "var(--gemma)",
  bonsai27Local: "var(--opencode)",
} satisfies Record<ModelKey, string>;
