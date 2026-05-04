/**
 * Confirms the Vite+Tailwind v4 bundle includes utilities used in React sources
 * and omits an unused utility (content scanning / tree-shaking).
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const cssPath = path.resolve(
  __dirname,
  "../../../django_apps/web/static/web/js/recipe_graph_editor/recipe-graph-editor.css",
);

const css = fs.readFileSync(cssPath, "utf8");

if (!css.includes("accent-cyan-500")) {
  console.error(
    "[verify-tailwind-purge] Built CSS missing accent-cyan-500 (expected from GraphEditorApp).",
  );
  process.exit(1);
}

if (css.includes("break-after-left")) {
  console.error(
    "[verify-tailwind-purge] Found break-after-left — likely unpurged; @source / scan may be wrong.",
  );
  process.exit(1);
}

console.log(
  `[verify-tailwind-purge] OK (${path.relative(process.cwd(), cssPath)}, ${css.length} bytes)`,
);
