import type { APIRoute } from "astro";

export const GET: APIRoute = () =>
  new Response(
    [
      "<!doctype html>",
      '<html lang="en">',
      "  <head>",
      '    <meta charset="utf-8" />',
      '    <meta http-equiv="refresh" content="0; url=/" />',
      '    <link rel="canonical" href="https://nixbench.com/" />',
      "    <title>Redirecting to NixBench</title>",
      "  </head>",
      "  <body>",
      '    <p>Redirecting to <a href="/">NixBench</a>.</p>',
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
