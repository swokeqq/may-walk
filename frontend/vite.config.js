import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// Dev-сервер запускается на 5500 (этот origin разрешён в CORS бэкенда),
// а запросы /api проксируются на FastAPI — cookie-сессия работает как same-origin.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const backendUrl = env.VITE_BACKEND_URL || "http://localhost:8000";
  const proxy = { "/api": { target: backendUrl, changeOrigin: true } };

  return {
    plugins: [react()],
    build: {
      rollupOptions: {
        output: { manualChunks: { ol: ["ol"], react: ["react", "react-dom"] } },
      },
    },
    server: { port: 5500, strictPort: true, proxy },
    preview: { port: 5500, strictPort: true, proxy },
  };
});
