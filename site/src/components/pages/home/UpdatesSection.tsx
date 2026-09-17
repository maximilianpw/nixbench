import { ArrowRight, Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

export type UpdatesSectionProps = {};

const quickCommand = "python3 bench.py run-all --agent-cmd 'your-agent-command-here'";

export function UpdatesSection({}: UpdatesSectionProps = {}) {
  const [copied, setCopied] = useState(false);

  async function copyCommand() {
    try {
      await navigator.clipboard.writeText(quickCommand);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section className="cta-band" id="updates" aria-labelledby="updates-heading">
      <div className="cta-band-inner">
        <div className="cta-copy">
          <h2 id="updates-heading">Run the benchmark yourself</h2>
          <p>Use the open-source harness to test another model, reproduce a result, or inspect every task.</p>
          <Button asChild variant="secondary">
            <a href="https://github.com/maximilianpw/nixbench#running-with-codex">
              Read the run guide <ArrowRight data-icon="inline-end" aria-hidden="true" />
            </a>
          </Button>
        </div>

        <aside className="command-card" aria-label="Quick start command">
          <div className="command-card-header">
            <span>Quick start</span>
            <Button type="button" variant="ghost" size="sm" onClick={copyCommand} aria-live="polite">
              {copied ? <Check data-icon="inline-start" aria-hidden="true" /> : <Copy data-icon="inline-start" aria-hidden="true" />}
              {copied ? "Copied" : "Copy"}
            </Button>
          </div>
          <code>{quickCommand}</code>
        </aside>
      </div>
    </section>
  );
}
