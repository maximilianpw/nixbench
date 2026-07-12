import type { APIRoute } from "astro";

import { getDocs } from "@/lib/docs";
import { siteMetadata } from "@/lib/seo";

function escapeXml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

export const GET: APIRoute = async ({ site }) => {
  const docs = await getDocs();
  const paths = ["/", "/results.html", ...docs.map((doc) => `/docs/${doc.pageSlug}.html`)];
  const baseUrl = site ?? new URL(siteMetadata.url);
  const entries = paths
    .map((path) => {
      const loc = new URL(path, baseUrl).toString();

      return [
        "  <url>",
        `    <loc>${escapeXml(loc)}</loc>`,
        `    <lastmod>${siteMetadata.lastUpdated}</lastmod>`,
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
