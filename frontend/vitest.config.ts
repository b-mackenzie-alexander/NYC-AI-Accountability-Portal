import { defineConfig } from "vitest/config";

export default defineConfig({
  css: {
    // These tests only exercise the API helper layer, so Vitest does not need
    // to load the app's PostCSS/Tailwind pipeline in CI.
    postcss: {
      plugins: [],
    },
  },
  test: {
    environment: "node",
  },
});
