import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/static/simulator-ui/",
  build: {
    outDir: "../../../ot_simulator/web_ui/static/simulator-ui",
    emptyOutDir: true,
  },
});
