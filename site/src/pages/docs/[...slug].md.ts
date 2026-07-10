import type { APIRoute, GetStaticPaths } from "astro";

import { getDocs, type DocPage } from "@/lib/docs";

export const getStaticPaths = (async () => {
  const docs = await getDocs();

  return docs.map((doc) => ({
    params: {
      slug: doc.pageSlug,
    },
    props: {
      doc,
    },
  }));
}) satisfies GetStaticPaths;

export const GET: APIRoute = ({ props }) => {
  const doc = props.doc as DocPage;
  const target = `/docs/${doc.pageSlug}.html`;

  return new Response(
    [
      `# ${doc.title}`,
      "",
      `This documentation page is now rendered as HTML at [${doc.title}](${target}).`,
      "",
    ].join("\n"),
    {
      headers: {
        "Content-Type": "text/markdown; charset=utf-8",
      },
    },
  );
};
