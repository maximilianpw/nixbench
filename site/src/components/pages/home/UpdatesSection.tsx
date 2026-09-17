import { ArrowRight, Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

const quickCommand = "python3 bench.py run-all --agent-cmd 'your-agent-command-here'";

export function UpdatesSection() {
  const [copied, setCopied] = useState(false);
  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(quickCommand);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch { setCopied(false); }
  }

  return (
    <section className="border-t bg-primary text-primary-foreground" id="updates" aria-labelledby="updates-heading">
      <div className="content-shell grid gap-8 py-16 lg:grid-cols-[0.8fr_1.2fr] lg:items-center">
        <div>
          <h2 id="updates-heading" className="text-3xl font-semibold tracking-tight sm:text-4xl">Run the benchmark yourself</h2>
          <p className="mt-4 max-w-xl text-primary-foreground/70">Use the open-source harness to test another model, reproduce a result, or inspect every task.</p>
          <Button asChild variant="secondary" className="mt-6"><a href="https://github.com/maximilianpw/nixbench#running-with-codex">Read the run guide <ArrowRight aria-hidden="true" /></a></Button>
        </div>
        <aside className="overflow-hidden rounded-lg border border-primary-foreground/20 bg-background text-foreground" aria-label="Quick start command">
          <div className="flex items-center justify-between border-b px-4 py-2">
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quick start</span>
            <Button type="button" variant="ghost" size="sm" onClick={copyCommand} aria-live="polite">{copied ? <Check aria-hidden="true" /> : <Copy aria-hidden="true" />}{copied ? "Copied" : "Copy"}</Button>
          </div>
          <code className="block overflow-x-auto border-0 bg-transparent p-5 text-sm">{quickCommand}</code>
        </aside>
      </div>
    </section>
  );
}
