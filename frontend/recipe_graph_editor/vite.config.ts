import path from "node:path";
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const staticOutDir = path.resolve(
  __dirname,
  "../../django_apps/web/static/web/js/recipe_graph_editor",
);

export default defineConfig({
  plugins: [tailwindcss(), react()],
  base: "/static/web/js/recipe_graph_editor/",
  build: {
    outDir: staticOutDir,
    emptyOutDir: true,
    sourcemap: true,
    cssCodeSplit: false,
    rollupOptions: {
      input: path.resolve(__dirname, "src/main.tsx"),
      output: {
        format: "es",
        entryFileNames: "recipe-graph-editor.js",
        chunkFileNames: "recipe-graph-editor-[name].js",
        assetFileNames: (assetInfo) => {
          const n = assetInfo.names?.[0] ?? assetInfo.name ?? "";
          if (typeof n === "string" && n.endsWith(".css")) {
            return "recipe-graph-editor.css";
          }
          return "recipe-graph-editor-assets/[name]-[hash][extname]";
        },
      },
    },
  },
});
