import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export type UpdatesSectionProps = {};

export function UpdatesSection({}: UpdatesSectionProps = {}) {
  return (
    <section className="cta-band" id="updates" aria-labelledby="updates-heading">
      <div>
        <p className="eyebrow">Run your agent</p>
        <h2 id="updates-heading">Add another row to the benchmark.</h2>
        <p>Use the local harness to run a CLI agent against the same copied worktree contract and hidden evaluator shape.</p>
      </div>
      <Button asChild>
        <a href="https://github.com/maximilianpw/nixbench#running-with-codex">
          Open run command <ArrowRight data-icon="inline-end" aria-hidden="true" />
        </a>
      </Button>
    </section>
  );
}
