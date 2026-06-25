import type { APIRoute } from "astro";

const siteUrl = "https://nixbench.com";
const lastmod = "2026-06-25";

const urls = [
  { path: "/", priority: "1.0" },
  { path: "/results.html", priority: "0.9" },
  { path: "/docs/benchmark-design.md", priority: "0.7" },
  { path: "/docs/running-agents.md", priority: "0.7" },
  { path: "/docs/task-format.md", priority: "0.6" },
  { path: "/docs/authoring.md", priority: "0.6" },
  { path: "/docs/scoring.md", priority: "0.6" },
  { path: "/docs/reproducibility.md", priority: "0.6" },
  { path: "/docs/research-derived-tasks.md", priority: "0.6" },
  { path: "/docs/runs/2026-06-24-model-comparison.md", priority: "0.5" },
];

function escapeXml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export const GET: APIRoute = () => {
  const entries = urls
    .map(({ path, priority }) => {
      const loc = new URL(path, siteUrl).toString();

      return [
        "  <url>",
        `    <loc>${escapeXml(loc)}</loc>`,
        `    <lastmod>${lastmod}</lastmod>`,
        `    <priority>${priority}</priority>`,
        "  </url>",
      ].join("\n");
    })
    .join("\n");

  return new Response(
    [
      '<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
      entries,
      "</urlset>",
      "",
    ].join("\n"),
    {
      headers: {
        "Content-Type": "application/xml; charset=utf-8",
      },
    },
  );
};
