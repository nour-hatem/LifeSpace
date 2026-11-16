import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

const DEFAULT_PROXY_TARGET = "http://127.0.0.1:8000";

export default defineConfig(({ mode }) => {
  const repositoryRoot = fileURLToPath(new URL("../..", import.meta.url));
  const fileEnv = loadEnv(mode, repositoryRoot, "");
  const proxyTarget =
    process.env.API_PROXY_TARGET ?? fileEnv.API_PROXY_TARGET ?? DEFAULT_PROXY_TARGET;

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: {
        "/api": {
          target: proxyTarget,
        },
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/test/setup.ts"],
    },
  };
});
