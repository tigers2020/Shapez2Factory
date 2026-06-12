/**
 * Node parity runner for lab_replay_overlay_bucket_registry.js vs Python registry.
 * Usage: echo '{"role":"paint_target","overlay":{...},"expected_kinds":[...]}' | node script
 * Or run via pytest which passes JSON array of cases on stdin.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const here = dirname(fileURLToPath(import.meta.url));
const jsPath = join(
  here,
  "..",
  "django_apps",
  "web",
  "static",
  "web",
  "js",
  "lab_replay_overlay_bucket_registry.js",
);
const code = readFileSync(jsPath, "utf8");
const sandbox = { globalThis: {} };
sandbox.globalThis = sandbox;
vm.runInNewContext(code, sandbox);
const mod = sandbox.LabReplayOverlayBucketRegistry;
if (!mod) {
  console.error("LabReplayOverlayBucketRegistry missing");
  process.exit(2);
}

const payload = JSON.parse(readFileSync(0, "utf8"));
const cases = Array.isArray(payload) ? payload : [payload];

for (const c of cases) {
  if (c.keys_role) {
    const got = mod.overlayBucketKeysForRole(c.keys_role);
    const want = c.expected_keys || [];
    if (got.length !== want.length || got.some((k, i) => k !== want[i])) {
      console.error(JSON.stringify({ case: c, got }));
      process.exit(1);
    }
    continue;
  }

  const overlay = c.overlay || {};
  const rows =
    c.role === "semantic_lookup"
      ? mod.collectOverlayCellsForSemanticLookup(overlay)
      : mod.collectOverlayCellsForPaintTarget(overlay);
  const kinds = rows
    .map((row) => String(row.cell_kind || row.kind || ""))
    .sort();
  const want = (c.expected_kinds || []).slice().sort();
  if (kinds.length !== want.length || kinds.some((k, i) => k !== want[i])) {
    console.error(JSON.stringify({ case: c, got: kinds }));
    process.exit(1);
  }
}
