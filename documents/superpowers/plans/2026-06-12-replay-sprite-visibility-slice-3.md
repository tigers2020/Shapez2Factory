# Replay Sprite Visibility — Slice 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** Swap canvas paint path to `LabReplayPaintPlan.buildLabPaintPlanFromFrame` behind `data-lab-paint-v2="1"` — **canvas only**, no DOM tone changes.

**Architecture:** `buildEffectiveCellViewIndex(frame)` → per-index `labPaintLayersFromView` → `canvasPlanFromPaintLayers` → existing `{overlays, sprites}` for `LabReplayCanvas.drawFrame`. Legacy `buildCanvasPaintPlan` remains fallback when flag absent/`0`.

**Spec:** [`documents/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md`](../specs/2026-06-12-replay-sprite-visibility-design.md)  
**Depends on:** Slice 2 commit (`lab_replay_paint_plan.js`, Python parity)

**Slice 3 stop:** V2 canvas path green with flag on; frame-38 anti-fade; golden smoke; legacy fallback unchanged when flag off. **No DOM / NON_SPRITE changes.**

---

## File map

| File | Change |
|------|--------|
| `django_apps/web/static/web/js/lab_replay_paint_plan.js` | `canvasPlanFromPaintLayers`, `buildLabPaintPlanFromFrame`, layout carry merge |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | `labPaintV2Enabled()`, delegate `buildCanvasPaintPlan` |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Optional: `data-lab-paint-v2="1"` on `#lab-root` for dev (or document flag only) |
| `tests/support/lab_replay_paint_plan.py` | `canvas_plan_from_paint_layers` Python mirror for tests |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py` | Adapter + frame-38 canvas plan tests |
| `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | JS contract: `buildLabPaintPlanFromFrame`, flag wiring |

---

## Adapter contract

```javascript
// LabPaintLayers → canvas plan entry
canvasPlanFromPaintLayers(layers, gridIdx) → { sprites: [...], overlays: [...] }

// candidate_ring chrome → overlay { idx, kind: "candidate_ring", stroke: "rgba(...)", fill: null }
// NO rgba fill when occupant or transport sprite present (anti-fade)
// Sprites: field_sprite + occupant + transport (stack order: terrain field_sprite drawn as sprite layer)
```

**Layout carry:** When current frame sparse, merge index keys from `buildEffectiveCellViewIndex(layoutFrame)` into current before adapter (union by cellKey).

**Feature flag:** `#lab-root dataset.labPaintV2 === "1"` enables v2; absent or `"0"` → legacy harvest plan.

---

### Task 1: Python canvas adapter mirror + tests

**Files:** `tests/support/lab_replay_paint_plan.py`, `tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py`

- [ ] `canvas_plan_from_paint_layers(layers, idx=0)` → `{sprites, overlays}`
- [ ] `test_frame_38_canvas_plan_has_miner_sprite_no_rgba_fill`
- [ ] `test_canvas_plan_anti_fade_no_fill_overlay_when_sprite`

Run: `pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py -v`

---

### Task 2: JS adapter + `buildLabPaintPlanFromFrame`

**Files:** `lab_replay_paint_plan.js`

- [ ] `canvasPlanFromPaintLayers(layers, gridIdx)`
- [ ] `buildLabPaintPlanFromFrame(frame, resolveCellIndex, options)` with carry merge
- [ ] Export on `LabReplayPaintPlan`

Contract tests in `test_lab_canvas_renderer.py`.

---

### Task 3: Wire flag + delegate in lab.js

**Files:** `asteroid_miner_layout_lab.js`

- [ ] `labPaintV2Enabled()` 
- [ ] `buildCanvasPaintPlan(frame)` → v2 when enabled else legacy
- [ ] Pass `resolveCellIndex` into v2 builder

**Do not** change `renderFullMapReplayFrame` DOM path.

---

### Task 4: Terrain canvas anti-fade (v2)

**Files:** `asteroid_miner_layout_lab.js` — `syncLabTerrainCanvasLayer` call sites when v2

When v2 + cell has field_sprite in paint plan, skip terrain rgba fill for that idx (or filter full_map cells using index).

---

### Task 5: Validation gate

```bash
python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py -q
python -m pytest tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py -q
```

Manual: enable `data-lab-paint-v2="1"`, frame 38 (10,7) sharp miner + ring.

---

## Out of scope (Slice 3)

- DOM chrome-only (Slice 4)
- Remove `NON_SPRITE_OVERLAY_CELL_KINDS` (Slice 4)
- Harvest quarantine delete (Slice 5)
- Default flag on in production template (optional dev-only)

---

## Execution

Subagent-Driven, Task 1 first.
