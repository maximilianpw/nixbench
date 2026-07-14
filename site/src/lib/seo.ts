export type StructuredData = Record<string, unknown>;

export const siteMetadata = {
  name: "NixBench",
  url: "https://nixbench.com/",
  description:
    "An open benchmark that measures how well AI coding agents write and repair Nix code using objective hidden evaluators.",
  socialImagePath: "/social-card.png",
  socialImageAlt: "NixBench — AI coding agent benchmark for Nix",
  lastUpdated: "2026-07-12",
} as const;

export const websiteStructuredData: StructuredData = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": `${siteMetadata.url}#website`,
  url: siteMetadata.url,
  name: siteMetadata.name,
  alternateName: "nixbench.com",
  description: siteMetadata.description,
  inLanguage: "en",
};

export function breadcrumbStructuredData(items: Array<{ name: string; url: string }>): StructuredData {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  };
}

export function serializeStructuredData(value: StructuredData) {
  return JSON.stringify(value).replaceAll("<", "\\u003c");
}
