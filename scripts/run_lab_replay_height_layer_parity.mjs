/**
 * Node parity runner for lab_replay_height_layer.js vs map_height_layer.py cases.
 * Usage: echo '[{...cases...}]' | node scripts/run_lab_replay_height_layer_parity.mjs
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
  "lab_replay_height_layer.js",
);
const code = readFileSync(jsPath, "utf8");
const sandbox = { globalThis: {} };
sandbox.globalThis = sandbox;
vm.runInNewContext(code, sandbox);
const mod = sandbox.LabReplayHeightLayer;
if (!mod) {
  console.error("LabReplayHeightLayer missing");
  process.exit(2);
}

const cases = JSON.parse(readFileSync(0, "utf8"));
for (const c of cases) {
  let got;
  if (c.output_transport_kind) {
    got = mod.enrichReplayWireRowWithLayer({
      cell_kind: c.cell_kind,
      transport_kind: c.transport_kind,
      output_transport_kind: c.output_transport_kind,
    }).layer;
  } else {
    got = mod.resolveReplayHeightLayer({
      cell_kind: c.cell_kind || "",
      transport_kind: c.transport_kind || "",
      tile_type: c.tile_type || "",
      layer: c.layer ?? undefined,
    });
  }
  if (got !== c.expected) {
    console.error(JSON.stringify({ case: c, got }));
    process.exit(1);
  }
}
