import { ArrowUpRight, FolderGit2 } from "lucide-react";

import { BrandMark } from "@/components/BrandMark";

type SiteFooterProps = { text: string; href: string; label: string };

export function SiteFooter({ text, href, label }: SiteFooterProps) {
  return (
    <footer className="border-t bg-card">
      <div className="content-shell grid gap-10 py-12 md:grid-cols-[1fr_auto] md:items-start">
        <div className="space-y-3">
          <a className="inline-flex items-center gap-2 font-semibold no-underline" href="/" aria-label="NixBench home">
            <BrandMark />
            <span>NixBench</span>
          </a>
          <p className="text-sm text-muted-foreground">An open benchmark for AI-written Nix.</p>
        </div>

        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm" aria-label="Footer">
          <a className="min-h-11 content-center text-muted-foreground hover:text-foreground" href="/results.html">Results</a>
          <a className="min-h-11 content-center text-muted-foreground hover:text-foreground" href="/docs/benchmark-design.html">Method</a>
          <a className="min-h-11 content-center text-muted-foreground hover:text-foreground" href="/docs/running-agents.html">Run guide</a>
          <a className="inline-flex min-h-11 items-center gap-1.5 text-muted-foreground hover:text-foreground" href="https://github.com/maximilianpw/nixbench">
            <FolderGit2 className="size-4" aria-hidden="true" /> GitHub <ArrowUpRight className="size-3.5" aria-hidden="true" />
          </a>
        </nav>
      </div>
      <div className="content-shell flex flex-col gap-2 border-t py-5 font-mono text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p dangerouslySetInnerHTML={{ __html: text }} />
        <a className="hover:text-foreground" href={href}>{label}</a>
      </div>
    </footer>
  );
}
