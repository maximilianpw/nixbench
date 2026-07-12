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
          <p>Objective evaluation for agent-written Nix.</p>
        </div>

        <nav className="footer-links" aria-label="Footer">
          <div>
            <span>Benchmark</span>
            <a href="/results.html">Results</a>
            <a href="/#leaderboard">Comparison rows</a>
            <a href="/#tasks">Task corpus</a>
          </div>
          <div>
            <span>Resources</span>
            <a href="/docs/benchmark-design.html">Methodology</a>
            <a href="/docs/running-agents.html">Run guide</a>
            <a href="https://github.com/maximilianpw/nixbench">GitHub</a>
          </div>
        </nav>
      </div>

      <div className="footer-bottom">
        <p dangerouslySetInnerHTML={{ __html: text }} />
        <a href={href}>{label}</a>
      </div>
    </footer>
  );
}
