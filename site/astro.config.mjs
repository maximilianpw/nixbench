import { defineConfig } from "astro/config";
import react from "@astrojs/react";

const isGitHubPagesBuild = process.env.GITHUB_ACTIONS === "true";

export default defineConfig({
  site: "https://maximilianpw.github.io",
  base: isGitHubPagesBuild ? "/nixbench" : "/",
  build: {
    format: "file",
  },
  integrations: [react()],
});
