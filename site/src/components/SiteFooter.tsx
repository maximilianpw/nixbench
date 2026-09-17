import { ArrowUpRight, FolderGit2 } from "lucide-react";

import { BrandMark } from "@/components/BrandMark";

type SiteFooterProps = {
  text: string;
  href: string;
  label: string;
};

export function SiteFooter({ text, href, label }: SiteFooterProps) {
  return (
    <footer className="site-footer">
      <div className="footer-shell">
        <div className="footer-brand">
          <a className="brand" href="/" aria-label="NixBench home">
            <BrandMark />
            <span className="brand-name">NixBench</span>
          </a>
          <p>An open benchmark for AI-written Nix.</p>
        </div>

        <nav className="footer-links" aria-label="Footer">
          <a href="/results.html">Results</a>
          <a href="/docs/benchmark-design.html">Method</a>
          <a href="/docs/running-agents.html">Run guide</a>
          <a className="footer-project-link" href="https://github.com/maximilianpw/nixbench">
            <FolderGit2 aria-hidden="true" />
            GitHub
            <ArrowUpRight aria-hidden="true" />
          </a>
        </nav>
      </div>

      <div className="footer-bottom">
        <p dangerouslySetInnerHTML={{ __html: text }} />
        <a href={href}>{label}</a>
      </div>
    </footer>
  );
}
