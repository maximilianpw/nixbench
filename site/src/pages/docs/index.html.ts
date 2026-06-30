import type { APIRoute } from "astro";

export const GET: APIRoute = () =>
  new Response(
    [
      "<!doctype html>",
      '<html lang="en">',
      "  <head>",
      '    <meta charset="utf-8" />',
      '    <meta http-equiv="refresh" content="0; url=/index.html" />',
      '    <link rel="canonical" href="/index.html" />',
      "    <title>Redirecting to NixBench</title>",
      "  </head>",
      "  <body>",
      '    <p>Redirecting to <a href="/index.html">NixBench</a>.</p>',
      "  </body>",
      "</html>",
      "",
    ].join("\n"),
    {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
      },
    },
  );
