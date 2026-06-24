import { defineConfig } from "astro/config";
import react from "@astrojs/react";

export default defineConfig({
  site: "https://nixbench.maximilian.pw",
  build: {
    format: "file",
  },
  integrations: [react()],
});
