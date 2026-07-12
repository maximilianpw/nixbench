import { ArrowUpRight, Menu, Moon, Sun, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { BrandMark } from "@/components/BrandMark";
import { Button } from "@/components/ui/button";

type ActivePage = "home" | "results" | "docs";

type NavItem = {
  label: string;
  href: string;
  activeOn?: ActivePage;
  external?: boolean;
};

const navItems: NavItem[] = [
  { label: "Overview", href: "/", activeOn: "home" },
  { label: "Results", href: "/results.html", activeOn: "results" },
  { label: "Tasks", href: "/#tasks" },
  { label: "Methodology", href: "/docs/benchmark-design.html", activeOn: "docs" },
  { label: "GitHub", href: "https://github.com/maximilianpw/nixbench", external: true },
] as const;

type AppHeaderProps = {
  activePage?: ActivePage;
};

export function AppHeader({ activePage }: AppHeaderProps) {
  const [theme, setThemeState] = useState<"light" | "dark">("light");
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    setThemeState(currentTheme);
  }, []);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    }

    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  function setTheme(nextTheme: "light" | "dark") {
    document.documentElement.dataset.theme = nextTheme;
    window.localStorage.setItem("nixbench-theme", nextTheme);
    document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')?.setAttribute(
      "content",
      nextTheme === "dark" ? "#101411" : "#f4f5f2",
    );
    setThemeState(nextTheme);
  }

  const nextTheme = theme === "dark" ? "light" : "dark";
  const themeLabel = ["Switch to", nextTheme, "theme"].join(" ");

  return (
    <header className="site-header">
      <div className="header-inner">
        <a className="brand" href="/" aria-label="NixBench home">
          <BrandMark />
          <span className="brand-name">NixBench</span>
        </a>

        <nav
          className="nav-links"
          id="primary-navigation"
          aria-label="Primary"
          data-open={menuOpen || undefined}
        >
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              aria-current={item.activeOn === activePage ? "page" : undefined}
              onClick={() => setMenuOpen(false)}
            >
              {item.label}
              {item.external ? <ArrowUpRight className="nav-external-icon" aria-hidden="true" /> : null}
            </a>
          ))}
          <Button asChild size="sm" className="nav-run">
            <a href="https://github.com/maximilianpw/nixbench#quick-start">Run NixBench</a>
          </Button>
        </nav>

        <div className="header-controls">
          <Button
            className="theme-toggle"
            type="button"
            variant="ghost"
            size="icon"
            aria-label={themeLabel}
            title={themeLabel}
            onClick={() => setTheme(nextTheme)}
          >
            {theme === "dark" ? (
              <Sun data-icon="only" aria-hidden="true" />
            ) : (
              <Moon data-icon="only" aria-hidden="true" />
            )}
          </Button>
          <Button
            ref={menuButtonRef}
            className="menu-toggle"
            type="button"
            variant="ghost"
            size="icon"
            aria-label={menuOpen ? "Close navigation" : "Open navigation"}
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? <X data-icon="only" aria-hidden="true" /> : <Menu data-icon="only" aria-hidden="true" />}
          </Button>
        </div>
      </div>
    </header>
  );
}
