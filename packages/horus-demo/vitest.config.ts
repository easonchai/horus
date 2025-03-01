import { defineConfig } from "vitest/config";
import swc from "unplugin-swc";

export default defineConfig({
  test: {
    testTimeout: 30000,
    globals: true,
    environment: "node",
    include: ["**/__tests__/**/*.test.ts", "test/**/*.test.ts"],
    coverage: {
      reporter: ["text", "json", "html"],
      include: ["src/**/*.ts"],
      exclude: ["src/**/*.d.ts", "src/**/__tests__/**"],
    },
  },
  plugins: [swc.vite()]
});
