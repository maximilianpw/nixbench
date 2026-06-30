import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";

type ActivePage = "home" | "results" | "docs";

type NavItem = {
  label: string;
  href: string;
  activeOn?: ActivePage;
};

const navItems: NavItem[] = [
  { label: "Runs", href: "/index.html#leaderboard" },
  { label: "Tasks", href: "/index.html#tasks" },
  { label: "Results", href: "/results.html", activeOn: "results" },
  { label: "Design", href: "/docs/benchmark-design.html", activeOn: "docs" },
  { label: "GitHub", href: "https://github.com/maximilianpw/nixbench" },
] as const;

type AppHeaderProps = {
  activePage: ActivePage;
};

export function AppHeader({ activePage }: AppHeaderProps) {
  const [theme, setThemeState] = useState<"light" | "dark">("light");

  useEffect(() => {
    const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    setThemeState(currentTheme);
  }, []);

  function setTheme(nextTheme: "light" | "dark") {
    document.documentElement.dataset.theme = nextTheme;
    window.localStorage.setItem("nixbench-theme", nextTheme);
    setThemeState(nextTheme);
  }

  const nextTheme = theme === "dark" ? "light" : "dark";
  const themeLabel = `Switch to ${nextTheme} theme`;

  return (
    <header className="site-header">
      <div className="header-inner">
        <a className="brand" href="/index.html" aria-label="NixBench home">
          <span className="brand-mark" aria-hidden="true">
            λ
          </span>
          <span>NixBench</span>
        </a>
        <nav className="nav-links" aria-label="Primary">
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              aria-current={item.activeOn === activePage ? "page" : undefined}
            >
              {item.label}
            </a>
          ))}
          <Button
            className="theme-toggle"
            type="button"
            variant="ghost"
            size="icon"
            aria-label={themeLabel}
            title={themeLabel}
            onClick={() => setTheme(nextTheme)}
          >
            {theme === "dark" ? <Sun data-icon="only" aria-hidden="true" /> : <Moon data-icon="only" aria-hidden="true" />}
          </Button>
        </nav>
      </div>
    </header>
  );
}
