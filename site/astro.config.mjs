import { defineConfig } from "astro/config";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://nixbench.com",
  build: {
    format: "file",
  },
  integrations: [react()],
});
