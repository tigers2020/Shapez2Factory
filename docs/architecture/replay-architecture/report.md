# Architecture Improvement Report — replay system

**Thread slug:** `replay-architecture`  
**Updated:** 2026-06-12  
**Kanban:** `.devtool/features/replay-architecture-2026-06-12.md`

## Scope

Holistic replay architecture review after recent `replay-cell-semantics` and `replay-sprite-visibility` slices. Focus: remaining scattered knowledge at wire read, height-layer (L=0/1/2), overlay harvest, and flat DOM paint index boundaries. **Review-only — no production edits.**

## Repository State

Clean worktree at `edd5cfe8`. `graphify-out/graph.json` is **GRAPH_STALE** (`224d6bac` vs HEAD). `graphify query` failed on Windows cp949 — evidence from grep/read/tests.

## Current Architecture Map

| Item | Finding |
|------|---------|
| Domain | Asteroid Lab product replay: solver runtime → timeline frames → Lab UI (detail + map paint) |
| Write path | `solver_runtime_assembler.py` → L2–L5 segment builders → `runtime_frame_finalize.py` → `overlay_wire_contract.py` (strict emission) + `map_height_layer.enrich_replay_wire_row_with_layer` |
| Wire DTOs | `timeline_dtos.py` ↔ `timeline_serialization.py` ↔ `replay_map_cell_wire.py` |
| Read semantics (delivered) | `replay_cell_semantics.py` + `lab_effective_cell_view.js` — kind/transport/occupant read policy |
| Read sanitize | `replay_wire_read_sanitize.py` + `lab_replay_wire_sanitize.js` — legacy candidate compat |
| Merge authority (delivered) | `effective_cell_view.py` + `lab_effective_cell_view.js` — `EffectiveCellView` for detail + paint |
| Paint authority (delivered) | `lab_replay_paint_plan.js` + `tests/support/lab_replay_paint_plan.py` — index → `LabPaintLayers` → canvas/DOM adapters |
| Overlay harvest (partial) | Python: `replay_overlay_bucket_registry.py` (role-based). JS paint: hardcoded subset in `overlayJsonRowsFromFrame` |
| Height layer (split) | Python: `map_height_layer.py` (write + tests). JS: `inferLabCellMapZ` in `asteroid_miner_layout_lab.js` (UI filter only) |
| Server cell lookup | `replay_frame_cell_resolver.py` — serialized frame → merge → `EffectiveCellWire` |
| UI shell | `asteroid_miner_layout_lab.js` — timeline chrome, Z filter, flat DOM grid, `frameCellIndexMap` → paint plan |
| Tests | Strong unit coverage per module; golden paint tests; `test_map_height_layer.py`; harvest quarantine guards |

```text
solver segments → frame finalize → wire JSON
                                      ↓
                    sanitize → merge (EffectiveCellView)
                                      ↓
              paint index (x,y,layer) → LabPaintLayers → render adapters
                                      ↓
              DOM grid (flat idx) + optional L filter (labCellMapZ)
```

## Complexity Symptoms and Red Flags

| Symptom / Red Flag | Evidence | Impact | Refactor Pressure |
|---|---|---|---|
| Information leakage — height layer | `map_height_layer.resolve_replay_height_layer` (Python) vs `inferLabCellMapZ` (JS, ~60 lines) | Drift risk; filter vs paint index disagree on legacy rows missing `layer` | High when adding kinds or transport aliases |
| Temporal decomposition — overlay harvest | Python paint uses `collect_overlay_cells_for_paint_target`; JS `overlayJsonRowsFromFrame` lists 5 keys manually | New overlay bucket visible in Python tests but invisible to browser paint until JS updated | Medium on every new bucket |
| Overexposure — paint index coords | `lab_replay_paint_plan.js` `cellCoord` uses `rowInt(row.layer)` default **0**; no inference | Rows without explicit `layer` collapse to L0 in index; co-located L1/L2 cells merge incorrectly | High for multi-plane cells at same (x,y) |
| Structural gap — flat DOM index | `buildCellByGridIndexFromFrame` → `resolveCellIndex({x,y,layer})` → single `Map` per grid idx | Last writer wins when “All layers” shown; filter hides cells but index still 2D | High for true multi-layer editing UX (non-goal today) |
| Repeated policy — explicit Z aliases | `wire_explicit_height_layer` (py) vs `wireExplicitLabCellMapZ` (js) — same `layer/L/z/Z` keys | Third copy if another consumer added | Low–medium |
| Python/JS parity tax | cell semantics, effective view, paint plan, wire sanitize already mirrored | Each new rule needs 2+ files + golden tests | Ongoing; pattern exists |

## Scattered Knowledge Found

| Shared Knowledge | Files / Areas | Current Risk |
|---|---|---|
| Height layer inference (L=0/1/2) | `map_height_layer.py`, `inferLabCellMapZ` in `asteroid_miner_layout_lab.js` | JS-only path for UI filter; paint index skips inference |
| Explicit layer alias keys | `wire_explicit_height_layer`, `wireExplicitLabCellMapZ` | Duplicated alias table |
| Output transport for layer resolution | `wire_transport_kind_for_layer_resolution` (py) vs inline candidate checks (js) | Candidate miner/stub plane selection |
| Overlay bucket harvest (paint role) | `replay_overlay_bucket_registry.py`, `overlayJsonRowsFromFrame` (js) | JS missing `equipment_bundles` and registry evolution |
| Effective cell index key | `replay_cell_index.cell_key`, `keyForCell` in paint JS | Aligned today; layer must be correct before keying |
| Kind / transport read policy | `replay_cell_semantics.py`, `lab_effective_cell_view.js` | **Delivered** — do not re-merge with height module |

| Question | Answer |
|----------|--------|
| What simple future change is currently hard? | Add a new overlay bucket or cell kind with correct L plane in browser paint + filter |
| How many places must change? | Python registry + wire emit + JS harvest list + JS inferLabCellMapZ + paint index (if layer missing) |
| What must callers know? | Whether `layer` on wire is authoritative; when inference runs (write vs UI filter only) |
| What is implicit or undocumented? | Paint index treats missing `layer` as 0; DOM grid is not layer-aware |
| Which dependency is non-obvious? | `wire_transport_kind_for_layer_resolution` for candidate rows |
| Organized by execution order? | Assembler L2→L5 temporal; acceptable. Overlay harvest split by consumer role is better but JS not wired |
| Common path expose rare features? | Z filter is isolated; paint index does not apply filter (correct) but also does not infer layer |
| Errors / special cases repeated? | Legacy missing `layer` handled differently in filter vs index |
| Module that should own height layer decision? | `map_height_layer` (extend to client mirror), not `asteroid_miner_layout_lab.js` |

## Better Together / Better Apart Decision

**Bring together:**

- Height layer explicit decode + inference + output-transport resolution (one policy)
- Overlay paint-target harvest keys + harvest order (registry already exists in Python)

**Keep apart:**

- `replay_cell_semantics` (kind/transport/occupant) — different lifecycle, already deep module
- `effective_cell_view` merge orchestration — consumes normalized rows, should not own plane inference
- `overlay_wire_contract` write strict profile — emit-time only
- Solver segment builders (L2–L5) — genuinely different domain knowledge
- DOM flat grid rendering — physical UI constraint; height module should not own DOM layout

**Chosen boundary:**

1. **Primary:** client-readable height-layer authority mirroring `map_height_layer.py`
2. **Secondary (small):** JS overlay harvest delegates to same bucket list as Python registry (generated list or shared manifest)

**Reason:**

Cell semantics and paint merge are solved. Remaining change amplification is **plane assignment** and **overlay bucket parity** on the browser read path — same pattern as the cell-semantics slice.

## Deep Module Candidate

**Proposed module:** `lab_replay_height_layer.js` (client mirror) + thin Python export hook; paint plan and lab shell call it instead of local inference.

**Owns:**

- `clamp` / explicit alias decode (`layer`, `L`, `z`, `Z`)
- `resolveReplayHeightLayer({ cell_kind, transport_kind, tile_type, layer })`
- `wireTransportKindForLayerResolution(row)` (candidate output transport)
- `enrichReplayWireRowWithLayer(row)` for read paths

**Hides:**

- Kind sets (`_SHAPE_FIELD_KINDS`, `_VOID_TRANSPORT_KINDS`, …)
- Tile heuristics (`SpaceBelt`, `Lift1`, …)
- Candidate miner/stub plane rules

**Exposes:**

- `resolveReplayHeightLayer(...)`
- `enrichReplayWireRowWithLayer(row)`
- `wireExplicitHeightLayer(row)`

**Does not expose:**

- Merge, paint layers, DOM grid indexing, write strict validation

**Caller responsibilities:**

- Paint index: enrich rows **before** `cellCoord` / `collectCoordUniverse`
- UI filter: `labCellMapZ(cell)` → delegate to module
- Do not re-implement kind lists in lab shell

**Module responsibilities:**

- Bit-for-bit parity with `map_height_layer.py` (golden vectors from `test_map_height_layer.py`)

**Invariants:**

- L ∈ {0,1,2}; explicit wire layer wins over inference
- Same inputs → same plane on Python write and JS read

**Default behavior:**

- Missing layer → infer from kind + transport + tile; clamp invalid

**Error policy:**

- Invalid numeric → clamp to 0 (match Python); no thrown errors on read

**Special-case policy:**

- `candidate_miner` / `candidate_transport_stub` use `output_transport_kind` when present (via `wire_transport_kind_for_layer_resolution`)

**Non-goals:**

- Layer-aware DOM grid or 3D cell elements
- Merging height policy into `replay_cell_semantics`
- Re-serializing all persisted frames server-side

### Interface Comment Draft

```text
Resolve Shapez 2 island height plane (L=0 floor, L=1 fluid, L=2 void transport)
for a replay wire cell row. Callers pass raw wire fields; module returns clamped L.
Explicit layer/L/z/Z on the row wins. Used before paint index keys and map Z filter.
Does not merge cells or paint sprites.
```

### Design Alternatives

#### Option A — JS mirror module (recommended)

- **Summary:** Port `map_height_layer.py` to `lab_replay_height_layer.js`; wire paint plan + lab shell.
- **Interface:** `enrichReplayWireRowWithLayer`, `resolveReplayHeightLayer`, `wireExplicitHeightLayer`
- **Common-case usage:** `const row = enrichReplayWireRowWithLayer(sanitizeCell(raw))` before index build
- **Rare-case usage:** UI filter calls `resolveReplayHeightLayer` only when debugging single row
- **Hides:** All kind/tile inference tables
- **Exposes:** 3 functions + constants for tests
- **Pros:** Matches proven cell-semantics pattern; fixes paint index default-0 bug; small diff
- **Cons:** Ongoing py/js parity maintenance
- **Failure mode:** Parity drift if tables edited in Python only

#### Option B — Server-only layer (reject for now)

- **Summary:** Require `layer` on all wire rows at serialize; client never infers
- **Pros:** Single Python authority
- **Cons:** Legacy persisted frames; client `map_view` fast-path; requires backfill migration
- **Failure mode:** Silent wrong paint for old artifacts

| Question | Option A | Option B |
|----------|----------|----------|
| Simpler common case for browser? | Yes | Yes (if migration done) |
| Hides implementation knowledge? | Yes | Yes |
| Avoids overexposing rare features? | Yes | N/A |
| Eliminates repeated special cases? | Yes (index + filter unified) | Partial |
| Avoids temporal decomposition? | Neutral | Neutral |
| Safer migration path? | Yes | No |

### Secondary slice — overlay harvest parity

- **Change:** Replace JS `overlayJsonRowsFromFrame` hardcoded keys with manifest from `overlay_bucket_keys_for_role(PAINT_TARGET)` (codegen script or checked-in JSON regenerated in CI)
- **Effort:** Small PR after height layer slice
- **Does not** need a new deep module if registry list is the single export

## Recommendation

1. **Next slice:** Option A — `lab_replay_height_layer.js` + paint-plan enrichment hook + delete `inferLabCellMapZ` / delegate `labCellMapZ`
2. **Follow-up:** Overlay harvest key parity (registry → JS manifest)
3. **Defer:** Layer-aware DOM grid — product/UX decision; document as known limitation in spec if multi-layer collision reported

Do **not** reopen `replay_cell_semantics` / merge / write contract unless height enrichment must run inside merge (prefer enrich **before** merge inputs).

## Minimal Change Plan

| Step | Action | Stop if |
|------|--------|---------|
| 1 | Add `lab_replay_height_layer.js` + load in lab template before paint plan | Parity vectors fail |
| 2 | Golden tests: port `test_map_height_layer` cases to JS (or shared JSON fixtures) | Any mismatch |
| 3 | `buildEffectiveCellViewIndex`: enrich full/overlay/delta/overlay-json rows before coord universe | Paint golden regress |
| 4 | Replace `inferLabCellMapZ` with module calls | `test_lab_canvas_renderer` token guards pass |
| 5 | Optional: Python `scripts/export_replay_overlay_paint_buckets.py` → JS include | Harvest quarantine tests fail |

One PR for steps 1–4; step 5 separate PR.

## Tests / Validation

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_map_height_layer.py -q
python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py -q
python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -q
```

Add: `test_lab_replay_height_layer_parity.py` (shared fixture table py↔js).

## Stop Conditions

- Parity cannot be maintained without codegen pipeline → stop and spec codegen approach
- Layer-aware DOM required for acceptance → escalate to UX spec (out of scope for height module)
- User wants server-only migration → rewrite plan as Option B with backfill contract

## Open Questions

1. Are persisted frames without `layer` still common in prod artifacts, or only legacy tests?
2. Should `enrichReplayWireRowWithLayer` run inside `sanitizeReplayWireCellForRead` (single read normalizer) vs paint index only?
3. Is multi-cell same `(x,y)` different L planes observed in live replay, or theoretical?

## Related completed threads (do not redo)

- `docs/architecture/replay-cell-semantics/` — read semantics module ✅
- `replay-sprite-visibility` — paint plan + anti-fade ✅
- `.devtool/features/replay-z-layer-review-2026-06-12.md` — informal Z audit ✅
