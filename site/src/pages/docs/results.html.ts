import type { APIRoute } from "astro";

export const GET: APIRoute = () =>
  new Response(
    [
      "<!doctype html>",
      '<html lang="en">',
      "  <head>",
      '    <meta charset="utf-8" />',
      '    <meta http-equiv="refresh" content="0; url=/results.html" />',
      '    <link rel="canonical" href="/results.html" />',
      "    <title>Redirecting to NixBench Results</title>",
      "  </head>",
      "  <body>",
      '    <p>Redirecting to <a href="/results.html">NixBench Results</a>.</p>',
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
