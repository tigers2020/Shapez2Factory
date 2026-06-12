# Replay Sprite Visibility — Slice 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** DOM chrome-only paint path when `data-lab-paint-v2="1"` — remove `candidate_miner` full-cell fill/tone on sprite cells; keep ring chrome + occupant sprite; preserve hit targets, detail lookup, canvas v2, and legacy fallback.

**Architecture:** Reuse Slice 2 merge → `labPaintLayersFromView` → **DOM adapter** (`domPlanFromPaintLayers`) → **frame-cached resolver** (`buildDomPlanResolverForFrame`). Effective-view index is built **once per render frame**, not per cell (avoids O(N²) in `renderFullMapCells`). `renderFullMapCells` / `labPaintTokenForCell` consult the resolver only when `labPaintV2Enabled()`; otherwise legacy harvest tone path unchanged. **Do not** change canvas v2, harvest authority, or detail lookup.

**Approved amendments (2026-06-12):**
1. Index/resolver built once per frame — no per-cell `buildEffectiveCellViewIndex`.
2. API: `buildDomPlanResolverForFrame(frame, options)` → `(cell) => domPlan | null` (no unused `resolveCellIndex`).
3. DOM sprite **occupant-only** — `spriteRel` from `occupant.rel` only; no new transport DOM sprite rendering.
4. Full-fill class checks use **exact class tokens** (split), not prefix substring — `lab-overlay-candidate-miner-ring` must not fail a naive `contains("lab-overlay-candidate-miner")` test.

**Tech Stack:** Python 3.12 pytest parity mirror, vanilla JS (`lab_replay_paint_plan.js` + `asteroid_miner_layout_lab.js`), existing CSS classes `lab-overlay-candidate-miner-ring` / `lab-overlay-candidate-miner`.

**Spec:** [`docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md`](../specs/2026-06-12-replay-sprite-visibility-design.md) §2.4 anti-fade, §2.6 DOM row  
**Depends on:** Slice 3 commit (`f099e7f4` — canvas v2 adapter + flag + terrain anti-fade)  
**Kanban:** `.devtool/features/replay-sprite-visibility-2026-06-12.md`

**Slice 4 stop:** Flag on → frame 38 `(10,7)` DOM has ring class + miner sprite, **no** `lab-overlay-candidate-miner` full-fill bg; flag off → legacy DOM unchanged; detail lookup untouched; canvas v2 untouched; harvest authority untouched.

---

## Hard boundaries (reviewer-locked)

```text
Allowed:
  DOM visual class / tone removal on v2 path
  candidate ring/stroke class on v2 path
  DOM occupant sprite from paint plan on v2 path

Forbidden (Slice 4):
  candidate_miner semantic removal from wire/merge
  labCellDetailLookupInMapView / mergeEffectiveCellView changes
  buildCanvasPaintPlan / buildLabPaintPlanFromFrame / filterTerrainCellsForPaintV2 changes
  collectFrameSpatialTargets / stageCell / frameCellIndexMap semantic changes
  harvest quarantine or delete (Slice 5)
  default data-lab-paint-v2="1" in production template
```

**DOM class vs semantic:** Removing `lab-overlay-candidate-miner` **background fill** on sprite cells is in scope. Removing `candidate_miner` from overlay wire, merge, or detail sources is **out of scope**.

**`NON_SPRITE_OVERLAY_CELL_KINDS`:** Do **not** delete `candidate_miner` from the set in the first green gate. V2 bypasses non-sprite DOM treatment when paint plan assigns an occupant sprite. Optional cleanup task runs **only after** full gate green (Task 7 — HITL).

---

## File map (Slice 4)

| File | Responsibility |
|------|----------------|
| `tests/support/lab_replay_paint_plan.py` | `dom_plan_from_paint_layers` Python mirror |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py` | Frame-38 DOM plan + anti-fade class tests |
| `django_apps/web/static/web/js/lab_replay_paint_plan.js` | `domPlanFromPaintLayers`, `buildEffectiveCellViewIndexWithCarry`, `buildDomPlanResolverForFrame` |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | V2 branch in `labPaintTokenForCell` + `renderFullMapCells`; DOM sprite apply from plan |
| `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | JS contract: dom adapter exports, v2 DOM wiring |
| `tests/unit/asteroid_lab/test_lab_renderer_token_diff.py` | Token-diff preserved; v2 token includes dom plan fields |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py` | Regression: paint layers unchanged (Slice 2 authority) |

**Forbidden edits:** `lab_replay_canvas_renderer.js`, `collectFrameSpatialTargets`, `buildCanvasPaintPlan` body (except unrelated imports), `labCellDetailLookupInMapView`.

---

## DOM adapter contract

```javascript
// LabPaintLayers → per-cell DOM paint instruction (dumb adapter)
domPlanFromPaintLayers(layers, opts?) → {
  toneClasses: string,       // e.g. "lab-overlay-candidate-miner-ring relative"
  spriteRel: string | null,  // OCCUPANT rel only — no transport DOM sprite in Slice 4
  spriteRotation: number,
  candidateObservation: boolean,
  skipFullFill: boolean,     // true when occupant OR transport sprite in layers (tone anti-fade)
}

// Frame → cached lookup (index built ONCE per frame)
buildDomPlanResolverForFrame(frame, options?) → function resolveDomPlan(cell) → domPlan | null

// Shared index builder (carry merge) — used by resolver, not per cell
buildEffectiveCellViewIndexWithCarry(frame, options?) → index object
```

**Performance rule:** `renderFullMapCells` must call `buildDomPlanResolverForFrame` **once before the cell loop**, then `resolveDomPlan(cell)` inside the loop. Same resolver instance passed into `labPaintTokenForCell` via closure or frame-scoped cache.

**DOM sprite scope (Slice 4):** Apply **occupant** sprite to DOM only. Transport sprites remain canvas path + existing legacy DOM behavior; do **not** introduce new transport DOM sprite rendering from `transport.rel`.

**Class token rule:** Tests and manual smoke must split `toneClasses` on whitespace and check exact tokens:

```python
tokens = set(plan["tone_classes"].split())
assert "lab-overlay-candidate-miner-ring" in tokens
assert "lab-overlay-candidate-miner" not in tokens  # ring token is NOT this standalone token
```

Do **not** use `"lab-overlay-candidate-miner" in tone_classes` substring checks — `lab-overlay-candidate-miner-ring` shares the prefix.

**Frame 38 `(10,7)` expected (v2):**

| Field | Value |
|-------|-------|
| `toneClasses` | `"lab-overlay-candidate-miner-ring relative"` |
| `spriteRel` | `"Miner/Layout_ShapeMiner.svg"` |
| `skipFullFill` | `true` |
| Must **not** contain token | `lab-overlay-candidate-miner` (standalone; ring token `lab-overlay-candidate-miner-ring` is OK) |

**Anti-fade:** If `spriteRel` set → `skipFullFill === true` and `toneClasses` must not imply rgba background (ring/stroke classes only). Full-fill class `lab-overlay-candidate-miner` is allowed only when **no** occupant/transport sprite in layers (void-only candidate observation).

**Legacy (flag off):** resolver not built; existing `toneForFullMapCell` → `lab-overlay-candidate-miner relative` + no sprite (NON_SPRITE) behavior preserved.

---

### Task 1: Python DOM adapter mirror + frame-38 tests

**Files:**
- Modify: `tests/support/lab_replay_paint_plan.py`
- Create: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py
from __future__ import annotations

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.effective_cell_wire import effective_cell_to_wire
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    sanitize_replay_wire_cell_for_read,
)
from tests.support.lab_replay_paint_fixtures import frame_38_candidate_miner_fixture
from tests.support.lab_replay_paint_plan import (
    dom_plan_from_paint_layers,
    lab_paint_layers_from_view,
)


def _merged_view_from_frame(frame: dict, x: int, y: int):
    mv = frame["map_view"]
    full = next(c for c in mv["full_cells"] if c["x"] == x and c["y"] == y)
    ov = next(c for c in mv["overlay_cells"] if c["x"] == x and c["y"] == y)
    view = merge_effective_cell_view(
        x=x,
        y=y,
        frame_index=int(frame.get("frame_index", 0)),
        full_cell=sanitize_replay_wire_cell_for_read(full),
        delta_cell=None,
        overlay_cells=[sanitize_replay_wire_cell_for_read(ov)],
    )
    assert view is not None
    return dict(effective_cell_to_wire(view))


def test_frame_38_dom_plan_ring_not_full_fill() -> None:
    wire = _merged_view_from_frame(frame_38_candidate_miner_fixture(), 10, 7)
    layers = lab_paint_layers_from_view(wire)
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["sprite_rel"] == "Miner/Layout_ShapeMiner.svg"
    assert plan["skip_full_fill"] is True
    assert "lab-overlay-candidate-miner-ring" in tokens
    assert "lab-overlay-candidate-miner" not in tokens


def test_dom_plan_anti_fade_no_full_fill_class_when_sprite() -> None:
    layers = {
        "terrain": {"mode": "field_sprite", "rel": "AsteroidField/AsteroidField_Shape.svg"},
        "occupant": {"rel": "Miner/Layout_ShapeMiner.svg", "rotation": 0},
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["skip_full_fill"] is True
    assert "lab-overlay-candidate-miner" not in tokens
    assert "lab-overlay-candidate-miner-ring" in tokens


def test_dom_plan_transport_does_not_set_sprite_rel() -> None:
    """Slice 4: skipFullFill may use transport for tone; spriteRel is occupant-only."""
    layers = {
        "terrain": None,
        "occupant": None,
        "transport": {"rel": "SpaceBelt/SpaceBelt_Forward.svg", "rotation": 0},
        "chrome": [],
    }
    plan = dom_plan_from_paint_layers(layers)
    assert plan["sprite_rel"] is None
    assert plan["skip_full_fill"] is True


def test_dom_plan_void_candidate_allows_full_fill_fallback() -> None:
    layers = {
        "terrain": None,
        "occupant": None,
        "transport": None,
        "chrome": [{"kind": "candidate_ring", "stroke_only": True}],
    }
    plan = dom_plan_from_paint_layers(layers, overlay_kind="candidate_miner")
    tokens = set(plan["tone_classes"].split())
    assert plan["sprite_rel"] is None
    assert plan["skip_full_fill"] is False
    assert "lab-overlay-candidate-miner" in tokens
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py -v`  
Expected: `ImportError` or `AttributeError: dom_plan_from_paint_layers`

- [ ] **Step 3: Implement Python adapter**

Add to `tests/support/lab_replay_paint_plan.py`:

```python
DOM_CANDIDATE_MINER_RING = "lab-overlay-candidate-miner-ring relative"
DOM_CANDIDATE_MINER_FILL = "lab-overlay-candidate-miner relative"


def _layers_have_sprite(layers: Mapping[str, object]) -> bool:
    """Tone anti-fade: occupant OR transport sprite blocks full-fill."""
    for slot in ("occupant", "transport"):
        entry = layers.get(slot)
        if isinstance(entry, Mapping) and entry.get("rel"):
            return True
    return False


def dom_plan_from_paint_layers(
    layers: Mapping[str, object],
    *,
    overlay_kind: str = "",
) -> dict[str, object]:
    occupant = layers.get("occupant")
    transport = layers.get("transport")
    chrome = layers.get("chrome")
    has_sprite = _layers_have_sprite(layers)
    has_candidate_ring = isinstance(chrome, list) and any(
        isinstance(c, Mapping) and c.get("kind") == "candidate_ring" for c in chrome
    )

    # Slice 4: DOM sprite is occupant-only (no transport.rel → sprite_rel)
    sprite_rel: str | None = None
    sprite_rotation = 0
    if isinstance(occupant, Mapping) and occupant.get("rel"):
        sprite_rel = str(occupant["rel"])
        sprite_rotation = _rotation(occupant)

    tone_classes = ""
    if has_candidate_ring:
        tone_classes = (
            DOM_CANDIDATE_MINER_RING if has_sprite else DOM_CANDIDATE_MINER_FILL
        )
    elif overlay_kind == "candidate_miner" and not has_sprite:
        tone_classes = DOM_CANDIDATE_MINER_FILL

    return {
        "tone_classes": tone_classes,
        "sprite_rel": sprite_rel,
        "sprite_rotation": sprite_rotation,
        "candidate_observation": has_candidate_ring or overlay_kind == "candidate_miner",
        "skip_full_fill": has_sprite,
    }
```

Update `__all__` to include `dom_plan_from_paint_layers`.

- [ ] **Step 4: Run — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py -v`  
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tests/support/lab_replay_paint_plan.py tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py
git commit -m "test(replay): Slice 4 DOM paint adapter parity (Python)"
```

---

### Task 2: JS DOM adapter + `buildDomPlanResolverForFrame`

**Files:**
- Modify: `django_apps/web/static/web/js/lab_replay_paint_plan.js`
- Test: `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`

- [ ] **Step 1: Write failing contract tests**

Add to `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`:

```python
def test_js_dom_plan_from_paint_layers_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function domPlanFromPaintLayers" in src
    assert "domPlanFromPaintLayers:" in src
    assert "lab-overlay-candidate-miner-ring" in src
    assert "skipFullFill" in src
    dom_body = src.split("function domPlanFromPaintLayers", 1)[1][:1200]
    assert "occupant" in dom_body
    assert "transport.rel" not in dom_body.replace("layersHaveSprite", "")


def test_js_build_dom_plan_resolver_for_frame_exists() -> None:
    src = PAINT_JS.read_text(encoding="utf-8")
    assert "function buildDomPlanResolverForFrame" in src
    assert "buildDomPlanResolverForFrame:" in src
    resolver_body = src.split("function buildDomPlanResolverForFrame", 1)[1][:900]
    assert "buildEffectiveCellViewIndexWithCarry" in resolver_body
    assert "return function" in resolver_body or "return function resolveDomPlan" in resolver_body
    assert "buildEffectiveCellViewIndex(frame)" not in resolver_body.split("return", 1)[0][-200:]
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py::test_js_dom_plan_from_paint_layers_exists tests/unit/asteroid_lab/test_lab_canvas_renderer.py::test_js_build_dom_plan_resolver_for_frame_exists -v`

- [ ] **Step 3: Implement JS adapter + frame resolver**

Add to `lab_replay_paint_plan.js`:

```javascript
  function buildEffectiveCellViewIndexWithCarry(frame, options) {
    options = options || {};
    var index = buildEffectiveCellViewIndex(frame);
    if (
      options.replayFrames &&
      options.hasServerReplay &&
      !indexHasSpriteCapableCells(index)
    ) {
      var replayArrayIndex =
        options.replayArrayIndex != null
          ? options.replayArrayIndex
          : options.replayFrames.length - 1;
      var layoutFrame = lastFrameWithSpriteCapableCells(
        options.replayFrames,
        replayArrayIndex
      );
      if (layoutFrame && layoutFrame !== frame) {
        index = mergeCarriedIndexKeys(
          buildEffectiveCellViewIndex(layoutFrame),
          index
        );
      }
    }
    return index;
  }

  function domPlanFromPaintLayers(layers, opts) {
    // ... same as Task 1 mirror; spriteRel from layers.occupant.rel ONLY
    // skipFullFill from layersHaveSprite (occupant OR transport for tone)
  }

  function buildDomPlanResolverForFrame(frame, options) {
    if (!frame) {
      return function () {
        return null;
      };
    }
    options = options || {};
    var index = buildEffectiveCellViewIndexWithCarry(frame, options);
    return function resolveDomPlan(cell) {
      if (!cell) return null;
      var layer = cell.layer != null ? cell.layer : 0;
      var key =
        typeof LabReplayWireSanitize !== "undefined" &&
        LabReplayWireSanitize.cellKey
          ? LabReplayWireSanitize.cellKey(cell.x, cell.y, layer)
          : String(cell.x) + "," + String(cell.y);
      var wire = index[key];
      if (!wire) return null;
      var layers = labPaintLayersFromView(wire);
      return domPlanFromPaintLayers(layers, {
        overlayKind: overlayCellKindFromWire(cell),
      });
    };
  }
```

Export on `LabReplayPaintPlan`:

```javascript
    domPlanFromPaintLayers: domPlanFromPaintLayers,
    buildEffectiveCellViewIndexWithCarry: buildEffectiveCellViewIndexWithCarry,
    buildDomPlanResolverForFrame: buildDomPlanResolverForFrame,
```

**Do not export** `buildDomPlanForCell(frame, cell, resolveCellIndex, ...)` — per-cell index rebuild forbidden.

- [ ] **Step 4: Run contract tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k "dom_plan" -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/web/static/web/js/lab_replay_paint_plan.js tests/unit/asteroid_lab/test_lab_canvas_renderer.py
git commit -m "feat(replay): Slice 4 JS DOM paint adapter"
```

---

### Task 3: Wire v2 DOM path in `labPaintTokenForCell` + `renderFullMapCells`

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Test: `tests/unit/asteroid_lab/test_lab_renderer_token_diff.py`, `test_lab_canvas_renderer.py`

- [ ] **Step 1: Write failing contract tests**

Add to `test_lab_canvas_renderer.py`:

```python
def test_lab_js_dom_paint_v2_wiring_in_token_and_render() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    token_body = src.split("function labPaintTokenForCell(", 1)[1].split("function frameCellIndexMap(", 1)[0]
    render_body = src.split("function renderFullMapCells(", 1)[1].split("function renderDiffOverlays(", 1)[0]
    assert "labPaintV2Enabled()" in token_body or "resolveDomPlan" in token_body
    assert "buildDomPlanResolverForFrame" in src
    assert "buildDomPlanResolverForFrame" in render_body
    assert render_body.index("buildDomPlanResolverForFrame") < render_body.index("for (let i = 0")
    assert "skipFullFill" in render_body or "domPlan" in render_body


def test_lab_js_detail_lookup_untouched() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    detail_body = src.split("function labCellDetailLookupInMapView(", 1)[1].split(
        "function labCellDetailFromTimelineFrame(", 1
    )[0]
    assert "LabReplayPaintPlan" not in detail_body
    assert "buildDomPlanResolverForFrame" not in detail_body
    assert "mergeEffectiveCellView" in detail_body
```

Add to `test_lab_renderer_token_diff.py`:

```python
def test_v2_dom_plan_included_in_render_token_when_enabled() -> None:
    src = JS.read_text(encoding="utf-8")
    token_body = src.split("function labPaintTokenForCell(", 1)[1].split("function frameCellIndexMap(", 1)[0]
    assert "domPlan" in token_body or "resolveDomPlan" in token_body
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py::test_lab_js_dom_paint_v2_wiring_in_token_and_render -v`

- [ ] **Step 3: Implement v2 DOM wiring (frame-scoped resolver)**

Add helpers near `labPaintV2Enabled()`:

```javascript
  function labDomPaintOptionsFromContext(frame) {
    return {
      replayFrames: replayFrames,
      replayArrayIndex: replayArrayIndex,
      hasServerReplay: hasServerReplay,
    };
  }

  function createDomPlanResolverForFrame(frame) {
    if (
      !labPaintV2Enabled() ||
      typeof LabReplayPaintPlan === "undefined" ||
      typeof LabReplayPaintPlan.buildDomPlanResolverForFrame !== "function"
    ) {
      return null;
    }
    return LabReplayPaintPlan.buildDomPlanResolverForFrame(
      frame,
      labDomPaintOptionsFromContext(frame),
    );
  }
```

**Modify `labPaintTokenForCell(cell, frame, domCells, idx, resolveDomPlan)`** — add optional 5th arg `resolveDomPlan` (frame-scoped resolver from caller):

```javascript
    if (resolveDomPlan) {
      const domPlan = resolveDomPlan(cell);
      if (domPlan) {
        const domTone = domPlan.toneClasses || "";
        const domSprite = domPlan.spriteRel || "";
        const domCand = domPlan.candidateObservation ? "1" : "0";
        return ck + "|" + role + "|" + rot + "|" + domSprite + "|" + domTone + "|" + domCand + "|v2";
      }
    }
```

**Modify `renderFullMapCells`** — build resolver **once before loop**:

```javascript
    const resolveDomPlan = createDomPlanResolverForFrame(frame);
    for (let i = 0; i < cells.length; i++) {
      ...
      const token = labPaintTokenForCell(cell, frame, domCells, idx, resolveDomPlan);
      ...
      const domPlan = resolveDomPlan ? resolveDomPlan(cell) : null;
      if (domPlan) {
        let tone = domPlan.toneClasses || toneForFullMapCell(cell, frame);
        // domPlan.toneClasses already ring-vs-fill from adapter; no substring fix needed
        el.className = tone ? base + " " + tone : base;
        ...
        if (domPlan.spriteRel) {
          applyLabCellSprite(el, {
            sprite_identifier: domPlan.spriteRel,
            rotation: domPlan.spriteRotation,
          }, frame);
        } else if (!domPlan.candidateObservation) {
          applyLabCellSprite(el, cell, frame);
        }
        renderedTokenByKey.set(idx, token);
        continue;
      }
      // legacy branch unchanged
    }
```

**Pass `resolveDomPlan`** into `resetDomCellsAtIndicesForFrame` / incremental reset if those call `labPaintTokenForCell` — or rebuild resolver once at `renderFullMapReplayFrame` level and thread through. Minimum: `renderFullMapCells` owns resolver; token helper accepts optional resolver param.

**Do not** call `buildEffectiveCellViewIndex` inside the cell loop.

- [ ] **Step 4: Run contract tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py::test_lab_js_dom_paint_v2_wiring_in_token_and_render tests/unit/asteroid_lab/test_lab_renderer_token_diff.py -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js tests/unit/asteroid_lab/test_lab_canvas_renderer.py tests/unit/asteroid_lab/test_lab_renderer_token_diff.py
git commit -m "feat(replay): Slice 4 v2 DOM chrome-only paint path"
```

---

### Task 4: Legacy fallback + paint-layer regression tests

**Files:**
- Modify: `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`
- Modify: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py` (smoke only)

- [ ] **Step 1: Add legacy fallback contract**

```python
def test_lab_js_legacy_dom_path_preserves_non_sprite_when_flag_off() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    rel_body = src.split("function labSpriteRelpathForCell(", 1)[1].split(
        "function attachLabSpriteImgNoDrag(", 1
    )[0]
    assert "isNonSpriteOverlayCell(cell, frame)" in rel_body
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "candidateObs" in render_body
    assert "lab-overlay-candidate-miner" in src
    non_sprite = src.split("var NON_SPRITE_OVERLAY_CELL_KINDS = {", 1)[1].split("};", 1)[0]
    assert "candidate_miner: true" in non_sprite


def test_lab_js_v2_dom_branch_gated_by_flag() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    resolver_body = src.split("function createDomPlanResolverForFrame(", 1)[1][:450]
    assert "labPaintV2Enabled()" in resolver_body
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "createDomPlanResolverForFrame" in render_body
    assert render_body.index("createDomPlanResolverForFrame") < render_body.index("for (let i = 0")
```

- [ ] **Step 2: Run paint-layer regression (Slice 2 authority unchanged)**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py -q`  
Expected: all passed (no paint resolver edits in Slice 4)

- [ ] **Step 3: Run new legacy tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k "legacy_dom or v2_dom_branch" -v`

- [ ] **Step 4: Commit**

```bash
git add tests/unit/asteroid_lab/test_lab_canvas_renderer.py
git commit -m "test(replay): Slice 4 legacy DOM fallback contracts"
```

---

### Task 5: Validation gate + manual smoke

- [ ] **Step 1: Full Slice 4 pytest gate**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  tests/unit/asteroid_lab/test_lab_renderer_token_diff.py \
  -q
```

Expected: all passed

- [ ] **Step 2: Slice 3 canvas regression (no canvas edits in Slice 4)**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py -k "canvas_plan or build_lab_paint or filter_terrain" \
  -q
```

Expected: all passed

- [ ] **Step 3: Slice 1 merge/sanitize regression**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py \
  -q
```

Expected: all passed

- [ ] **Step 4: Manual smoke (dev opt-in flag)**

1. Set `data-lab-paint-v2="1"` on `#lab-root` in `asteroid_miner_layout_solver.html` **locally only** (do not commit as default).
2. Load solver replay; seek frame 38; inspect cell `(10,7)`:
   - DOM classList tokens: must include `lab-overlay-candidate-miner-ring`
   - DOM classList tokens: must **not** include standalone token `lab-overlay-candidate-miner` (do not use substring check — ring token shares prefix)
   - Sprite: `Layout_ShapeMiner` visible in `.lab-cell-sprite`
   - Canvas: unchanged from Slice 3 (sharp miner + ring overlay)
3. Remove flag → legacy full-fill + no DOM miner sprite restored.

- [ ] **Step 5: Update kanban + final commit if smoke OK**

Update `.devtool/features/replay-sprite-visibility-2026-06-12.md` Progress with gate evidence.

```bash
git add .devtool/features/replay-sprite-visibility-2026-06-12.md docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-4.md
git commit -m "docs(replay): Slice 4 DOM chrome-only plan complete"
```

---

### Task 7 (optional, HITL after Task 5 green): `NON_SPRITE` candidate_miner cleanup

**Only proceed if user approves after Slice 4 gate.**

- [ ] Remove `candidate_miner: true` from `NON_SPRITE_OVERLAY_CELL_KINDS` in `asteroid_miner_layout_lab.js`
- [ ] Remove from `tests/support/lab_replay_sprite_wire.py` `NON_SPRITE_OVERLAY_CELL_KINDS` frozenset
- [ ] Add explicit `if (!labPaintV2Enabled() && ck === "candidate_miner")` legacy guard in `isNonSpriteOverlayCell` if needed for flag-off parity
- [ ] Re-run full gate + manual flag-off smoke

**Do not start Task 7 during initial Subagent-Driven Slice 4 execution.**

---

## Out of scope (Slice 4)

- Canvas plan / terrain filter changes (Slice 3 — frozen)
- Harvest quarantine / delete (Slice 5)
- Playwright PNG regression
- Default production flag enablement
- Transport DOM sprite (unless already in effective view for non-candidate cells — use existing legacy path)

---

## Self-review (plan author checklist)

| Spec requirement | Task |
|------------------|------|
| DOM chrome-only for candidate_miner | Task 1–3 |
| Anti-fade: no bg tone over sprite | Task 1 tests, Task 3 `skipFullFill` |
| Feature flag gating | Task 3 `resolveDomPlanForCell` |
| Detail lookup preserved | Task 3 contract + forbidden edits |
| Canvas v2 unchanged | Forbidden edits |
| Legacy fallback | Task 4 |
| NON_SPRITE gradual cleanup | Task 7 optional HITL |
| Harvest untouched | Hard boundaries |

No TBD / implement-later placeholders in task steps.

---

## Execution handoff

**Plan saved:** `docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-4.md`

**Plan approved with amendments (2026-06-12).** Execute via Subagent-Driven, Tasks 1→5 only; skip Task 7.
