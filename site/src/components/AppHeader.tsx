import { ArrowUpRight, FolderGit2, Menu, Moon, Sun, X } from "lucide-react";
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
  { label: "Results", href: "/results.html", activeOn: "results" },
  { label: "Tasks", href: "/#tasks" },
  { label: "Method", href: "/docs/benchmark-design.html", activeOn: "docs" },
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
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="content-shell flex h-16 items-center gap-4">
        <a className="flex items-center gap-2 font-semibold no-underline" href="/" aria-label="NixBench home">
          <BrandMark />
          <span>NixBench</span>
        </a>

        <nav
          className="ml-auto hidden items-center gap-1 md:flex data-[open=true]:absolute data-[open=true]:inset-x-0 data-[open=true]:top-16 data-[open=true]:flex data-[open=true]:flex-col data-[open=true]:items-stretch data-[open=true]:border-b data-[open=true]:bg-background data-[open=true]:p-4 md:data-[open=true]:static md:data-[open=true]:flex-row md:data-[open=true]:border-0 md:data-[open=true]:p-0"
          id="primary-navigation"
          aria-label="Primary"
          data-open={menuOpen || undefined}
        >
          {navItems.map((item) => (
            <a
              key={item.label}
              href={item.href}
              aria-current={item.activeOn === activePage ? "page" : undefined}
              className="flex min-h-11 items-center rounded-md px-3 text-sm font-medium text-muted-foreground no-underline hover:bg-muted hover:text-foreground aria-[current=page]:text-foreground aria-[current=page]:shadow-[inset_0_-2px_0_var(--nix-blue)]"
              onClick={() => setMenuOpen(false)}
            >
              {item.label}
              {item.external ? <ArrowUpRight className="ml-1 size-3.5" aria-hidden="true" /> : null}
            </a>
          ))}
          <Button asChild size="sm">
            <a href="https://github.com/maximilianpw/nixbench">
              <FolderGit2 data-icon="inline-start" aria-hidden="true" />
              Project <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
            </a>
          </Button>
        </nav>

        <div className="ml-auto flex items-center gap-1 md:ml-0">
          <Button
            className="ml-0 md:ml-2"
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
            className="md:hidden"
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
