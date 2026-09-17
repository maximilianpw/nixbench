import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://nixbench.com",
  build: {
    format: "file",
  },
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
});
