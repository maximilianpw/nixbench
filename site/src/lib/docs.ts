import { readdir, readFile } from "node:fs/promises";
import { join, relative, resolve, sep } from "node:path";

export type DocHeading = {
  depth: 2 | 3;
  id: string;
  text: string;
};

export type DocPage = {
  slug: string;
  pageSlug: string;
  title: string;
  summary: string;
  group: string;
  sourcePath: string;
  headings: DocHeading[];
  html: string;
};

const docsRoot = resolve(process.cwd(), "../docs");

const preferredOrder = [
  "benchmark-design.md",
  "running-agents.md",
  "task-format.md",
  "authoring.md",
  "scoring.md",
  "reproducibility.md",
  "research-derived-tasks.md",
  "runs/2026-06-24-model-comparison.md",
];

const orderBySlug = new Map(preferredOrder.map((slug, index) => [slug, index]));

async function listMarkdownFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(
    entries.map(async (entry) => {
      const fullPath = join(directory, entry.name);

      if (entry.isDirectory()) {
        return listMarkdownFiles(fullPath);
      }

      return entry.isFile() && entry.name.endsWith(".md") ? [fullPath] : [];
    }),
  );

  return files.flat();
}

function sortDocs(a: string, b: string) {
  const aOrder = orderBySlug.get(a) ?? Number.MAX_SAFE_INTEGER;
  const bOrder = orderBySlug.get(b) ?? Number.MAX_SAFE_INTEGER;

  return aOrder === bOrder ? a.localeCompare(b) : aOrder - bOrder;
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeAttribute(value: string) {
  return escapeHtml(value).replaceAll("`", "&#96;");
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function ensureUniqueSlug(value: string, usedIds: Map<string, number>) {
  const base = slugify(value) || "section";
  const count = usedIds.get(base) ?? 0;
  usedIds.set(base, count + 1);

  return count === 0 ? base : `${base}-${count + 1}`;
}

function renderInline(value: string) {
  const codeTokens: string[] = [];
  const tokenized = value.replace(/`([^`]+)`/g, (_, code: string) => {
    const token = `\uE000${codeTokens.length}\uE000`;
    codeTokens.push(`<code>${escapeHtml(code)}</code>`);
    return token;
  });

  const linked = escapeHtml(tokenized)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label: string, href: string) => {
      const escapedHref = escapeAttribute(href);
      const target = /^https?:\/\//.test(href) ? ' target="_blank" rel="noreferrer"' : "";

      return `<a href="${escapedHref}"${target}>${label}</a>`;
    })
    .replace(/(^|[\s(])(https?:\/\/[^\s)]+)/g, (_, prefix: string, url: string) => {
      const trailing = /[.,;:]$/.test(url) ? url.slice(-1) : "";
      const href = trailing ? url.slice(0, -1) : url;

      return `${prefix}<a href="${escapeAttribute(href)}" target="_blank" rel="noreferrer">${href}</a>${trailing}`;
    });

  return codeTokens.reduce((html, token, index) => html.replaceAll(`\uE000${index}\uE000`, token), linked);
}

function splitTableRow(value: string) {
  return value
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function isTableDivider(value: string) {
  return splitTableRow(value).every((cell) => /^:?-{3,}:?$/.test(cell));
}

function renderTable(lines: string[]) {
  const headers = splitTableRow(lines[0] ?? "");
  const rows = lines.slice(2).map(splitTableRow);

  return [
    '<div class="docs-table-wrap">',
    '  <table class="table docs-table">',
    "    <thead>",
    `      <tr>${headers.map((header) => `<th>${renderInline(header)}</th>`).join("")}</tr>`,
    "    </thead>",
    "    <tbody>",
    ...rows.map((row) => `      <tr>${row.map((cell) => `<td>${renderInline(cell)}</td>`).join("")}</tr>`),
    "    </tbody>",
    "  </table>",
    "</div>",
  ].join("\n");
}

function renderList(lines: string[], ordered: boolean) {
  const items = lines.map((line) => {
    const text = ordered ? line.replace(/^\d+\.\s+/, "") : line.replace(/^[-*]\s+/, "");
    return `<li>${renderInline(text)}</li>`;
  });

  return `<${ordered ? "ol" : "ul"}>\n${items.join("\n")}\n</${ordered ? "ol" : "ul"}>`;
}

function renderMarkdown(markdown: string) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const usedIds = new Map<string, number>();
  const headings: DocHeading[] = [];
  const html: string[] = [];
  let index = 0;
  let skippedTitle = false;

  while (index < lines.length) {
    const line = lines[index] ?? "";
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    const heading = /^(#{1,3})\s+(.+)$/.exec(trimmed);
    if (heading) {
      const depth = heading[1].length;
      const text = heading[2].trim();

      if (depth === 1 && !skippedTitle) {
        skippedTitle = true;
        index += 1;
        continue;
      }

      if (depth === 2 || depth === 3) {
        const id = ensureUniqueSlug(text, usedIds);
        headings.push({ depth, id, text });
        html.push(`<h${depth} id="${id}">${renderInline(text)}</h${depth}>`);
      }

      index += 1;
      continue;
    }

    if (trimmed.startsWith("```")) {
      const language = trimmed.slice(3).trim();
      const code: string[] = [];
      index += 1;

      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        code.push(lines[index] ?? "");
        index += 1;
      }

      index += 1;
      html.push(`<pre data-language="${escapeAttribute(language)}"><code>${escapeHtml(code.join("\n"))}</code></pre>`);
      continue;
    }

    if (trimmed.startsWith("|") && lines[index + 1] && isTableDivider(lines[index + 1])) {
      const tableLines = [trimmed, lines[index + 1].trim()];
      index += 2;

      while (index < lines.length && lines[index].trim().startsWith("|")) {
        tableLines.push(lines[index].trim());
        index += 1;
      }

      html.push(renderTable(tableLines));
      continue;
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const listLines: string[] = [];

      while (index < lines.length && /^[-*]\s+/.test(lines[index].trim())) {
        listLines.push(lines[index].trim());
        index += 1;
      }

      html.push(renderList(listLines, false));
      continue;
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const listLines: string[] = [];

      while (index < lines.length && /^\d+\.\s+/.test(lines[index].trim())) {
        listLines.push(lines[index].trim());
        index += 1;
      }

      html.push(renderList(listLines, true));
      continue;
    }

    if (trimmed.startsWith(">")) {
      const quoteLines: string[] = [];

      while (index < lines.length && lines[index].trim().startsWith(">")) {
        quoteLines.push(lines[index].trim().replace(/^>\s?/, ""));
        index += 1;
      }

      html.push(`<blockquote>${renderInline(quoteLines.join(" "))}</blockquote>`);
      continue;
    }

    const paragraph: string[] = [];

    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^(#{1,3})\s+/.test(lines[index].trim()) &&
      !lines[index].trim().startsWith("```") &&
      !lines[index].trim().startsWith("|") &&
      !/^[-*]\s+/.test(lines[index].trim()) &&
      !/^\d+\.\s+/.test(lines[index].trim()) &&
      !lines[index].trim().startsWith(">")
    ) {
      paragraph.push(lines[index].trim());
      index += 1;
    }

    html.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
  }

  return {
    headings,
    html: html.join("\n"),
  };
}

function extractTitle(markdown: string, slug: string) {
  const title = /^#\s+(.+)$/m.exec(markdown)?.[1]?.trim();

  return title ?? slug.replace(/\.md$/, "").split("/").pop()?.replaceAll("-", " ") ?? slug;
}

function extractSummary(markdown: string) {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const firstParagraph = lines.find((line) => {
    const trimmed = line.trim();
    return trimmed && !trimmed.startsWith("#") && !trimmed.startsWith("```") && !trimmed.startsWith("|");
  });

  return firstParagraph?.trim() ?? "NixBench documentation.";
}

function docGroup(slug: string) {
  return slug.startsWith("runs/") ? "Run Notes" : "Guide";
}

export async function getDocs() {
  const files = await listMarkdownFiles(docsRoot);
  const docs = await Promise.all(
    files.map(async (file) => {
      const slug = relative(docsRoot, file).split(sep).join("/");
      const markdown = await readFile(file, "utf8");
      const rendered = renderMarkdown(markdown);

      return {
        slug,
        pageSlug: slug.replace(/\.md$/, ""),
        title: extractTitle(markdown, slug),
        summary: extractSummary(markdown),
        group: docGroup(slug),
        sourcePath: `docs/${slug}`,
        headings: rendered.headings,
        html: rendered.html,
      } satisfies DocPage;
    }),
  );

  return docs.sort((a, b) => sortDocs(a.slug, b.slug));
}
