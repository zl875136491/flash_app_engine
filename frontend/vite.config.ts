import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";
import { VitePWA } from "vite-plugin-pwa";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const certDir = path.resolve(rootDir, "../certs");
const certFile = path.join(certDir, "ip.crt");
const keyFile = path.join(certDir, "ip.key");

function httpsOption() {
  const enabled = (process.env.VITE_HTTPS || "true").toLowerCase() !== "false";
  if (!enabled) return undefined;
  if (!fs.existsSync(certFile) || !fs.existsSync(keyFile)) {
    console.warn(
      "[vite] 未找到 ../certs/ip.crt 与 ip.key，将以 HTTP 启动。请运行 ./scripts/gen-ip-certs.sh <IP>",
    );
    return undefined;
  }
  return {
    cert: fs.readFileSync(certFile),
    key: fs.readFileSync(keyFile),
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, rootDir, "");
  const apiTarget = env.VITE_API_PROXY_TARGET || process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
  const https = httpsOption();

  return {
    plugins: [
      react(),
      tailwindcss(),
      VitePWA({
        registerType: "autoUpdate",
        includeAssets: ["favicon.svg", "apple-touch-icon.png"],
        manifest: {
          name: "FlashApp Engine",
          short_name: "FlashApp",
          description: "口述即部署的内网轻量云计算平台",
          theme_color: "#5ec992",
          background_color: "#ffffff",
          display: "standalone",
          orientation: "portrait",
          start_url: "/",
          lang: "zh-CN",
          icons: [
            {
              src: "pwa-192.png",
              sizes: "192x192",
              type: "image/png",
            },
            {
              src: "pwa-512.png",
              sizes: "512x512",
              type: "image/png",
            },
            {
              src: "pwa-512.png",
              sizes: "512x512",
              type: "image/png",
              purpose: "maskable",
            },
          ],
        },
        workbox: {
          navigateFallback: "/index.html",
          globPatterns: ["**/*.{js,css,html,ico,png,svg,woff2}"],
        },
        devOptions: {
          enabled: false,
        },
      }),
    ],
    resolve: {
      alias: {
        "@": path.resolve(rootDir, "./src"),
      },
    },
    server: {
      host: process.env.VITE_DEV_HOST || "0.0.0.0",
      port: Number(process.env.VITE_DEV_PORT || 5173),
      https,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          secure: false, // 允许代理到自签 HTTPS 后端
          ws: true,
        },
      },
    },
    preview: {
      host: process.env.VITE_DEV_HOST || "0.0.0.0",
      port: Number(process.env.VITE_PREVIEW_PORT || 4173),
      https,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          ws: true,
        },
      },
    },
  };
});
