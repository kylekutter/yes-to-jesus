import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds a single self-contained IIFE bundle so the plain static site can
// load it with one <script> tag — no module system or bundler needed on
// the page itself.
export default defineConfig({
  plugins: [react()],
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    outDir: "../static/js/widget-dist",
    emptyOutDir: true,
    cssCodeSplit: false,
    lib: {
      entry: "src/main.tsx",
      name: "YesToJesusScriptureWidget",
      formats: ["iife"],
      fileName: () => "scripture-widget.js",
    },
    rollupOptions: {
      output: {
        assetFileNames: "scripture-widget.[ext]",
      },
    },
  },
});
