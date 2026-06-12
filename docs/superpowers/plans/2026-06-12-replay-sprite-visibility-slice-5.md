# Replay Sprite Visibility — Slice 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quarantine then remove **harvest paint authority** (`collectFrameSpatialTargets` / `stageCell` / `labSpriteRelpathForCell` paint semantics) after v2 paint path (Slices 2–4) is proven; migrate remaining call sites to EffectiveCellView-driven helpers; enable safe cleanup of legacy fallbacks including Slice 4 Task 7 `NON_SPRITE` policy.

**Architecture:** Harvest functions become **deprecated spatial collectors only** (or deleted). Paint/canvas/DOM sprite decisions flow exclusively: sanitize → merge → `labPaintLayersFromView` → canvas/DOM adapters. Non-paint uses (grid bbox, preload rel set) get dedicated helpers that do **not** reinterpret occupant/transport/candidate. Feature flag `data-lab-paint-v2="1"` remains rollback until delete phase completes; default-on in production template is **HITL** (separate from this slice's code delete).

**Tech Stack:** Python 3.12 pytest, vanilla JS (`lab_replay_paint_plan.js`, `asteroid_miner_layout_lab.js`), static contract tests in `test_lab_canvas_renderer.py`.

**Spec:** [`docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md`](../specs/2026-06-12-replay-sprite-visibility-design.md) §2.1 hard rule, §2.7 quarantine, §3.3 Slice 5  
**Depends on:** Slice 4 commits (`d9cdd73e`…`3a0d60ee`) — v2 canvas + DOM green  
**Kanban:** `.devtool/features/replay-sprite-visibility-2026-06-12.md`

**Slice 5 stop (Tasks 1→5):** All **v2-enabled** paths use paint-plan module only; harvest quarantined and marked; carry/preload/index migrated under v2; Python golden uses paint plan. **Flag-off legacy canvas/DOM harvest may still exist** — that removal is Task 6 HITL.

**Approved amendments (2026-06-12 plan review):**

1. **Task 5 ≠ full delete.** Tasks 1→5 migrate v2 paths only; flag-off legacy stays until Task 6 HITL. No `throw` on `!labPaintV2Enabled()` unless policy **(B)** explicitly approved (template has no v2 flag today).
2. **`buildCellByGridIndexFromFrame`** — index once per frame (Slice 4 performance rule).
3. **Task 1 DOM audit** — reliable `if (domPlan)` block scan, not `// legacy` anchor.
4. **Task 5 default policy (A) soft quarantine**; hard delete → Task 6.

**Plan review:** APPROVED WITH AMENDMENTS — Tasks 1→5 executable on command; Task 6/7 HITL.

---

## Harvest inventory (current)

| Symbol | File | Role today | Slice 5 fate |
|--------|------|------------|--------------|
| `collectFrameSpatialTargets` | `lab.js` | Flat wire union (full/overlay/delta/diff/overlay_json) | Quarantine → delete paint uses; keep thin spatial union for **bbox only** if needed |
| `stageCell` | `lab.js` (inside `buildCanvasPaintPlan`) | Legacy canvas paint staging + `labSpriteRelpathForCell` | **Delete** when v2-only canvas |
| `labSpriteRelpathForCell` | `lab.js` | Harvest sprite resolve; NON_SPRITE skips candidate | Quarantine → delete paint uses; legacy DOM flag-off until delete phase |
| `frameCellIndexMap` | `lab.js` | idx→cell via harvest (DOM token reset) | Migrate to effective-view index lookup |
| `frameHasSpriteCapableCells` | `lab.js` (canvas closure) | Duplicate of paint-plan carry probe | Replace with `LabReplayPaintPlan.indexHasSpriteCapableCells` |
| `lastFrameWithSpriteCapableCells` | `lab.js` (canvas closure) | Duplicate carry | Replace with paint-plan export |
| `collectSpriteRelpathsFromFrames` | `lab.js` | Preload via harvest + `labSpriteRelpathForCell` | Migrate to v2 paint plan sprite rels |
| `computeReplayGridLayout` | `lab.js` | Bbox from harvest targets | **Not paint semantics** — may keep spatial union helper with rename |
| `collect_frame_spatial_targets` | `lab_replay_sprite_wire.py` | Python harvest mirror | Deprecate paint parity; migrate `sprite_paint_entries_for_frame` |
| `sprite_paint_entries_for_frame` | `lab_replay_sprite_wire.py` | Golden harvest sprite list | Rewrite using `build_effective_cell_view_index` + `lab_paint_layers_from_view` |

**Hard rule (unchanged):** Harvest must not decide occupant vs transport vs candidate after Slice 5.

---

## Hard boundaries

```text
Allowed:
  @deprecated markers + quarantine module/wrapper
  Migrate call sites to LabReplayPaintPlan / buildDomPlanResolverForFrame
  Delete legacy buildCanvasPaintPlan harvest branch (after gate)
  Slice 4 Task 7 NON_SPRITE cleanup in delete subtask only (HITL)

Forbidden (until delete subtask + HITL):
  Default data-lab-paint-v2="1" in production template without review
  Removing candidate_miner semantic from wire/merge/detail
  Changing sanitizer / EffectiveCellView merge authority
  Deleting computeReplayGridLayout spatial union without bbox replacement test
```

**Task 7 (Slice 4) relationship:** `NON_SPRITE_OVERLAY_CELL_KINDS.candidate_miner` removal happens in **Slice 5 Task 6 (HITL delete subtask)** only after harvest delete policy is implemented and flag-off legacy path is gone.

---

## File map

| File | Change |
|------|--------|
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Quarantine markers; migrate call sites; delete harvest paint branch |
| `django_apps/web/static/web/js/lab_replay_paint_plan.js` | Export shared carry/sprite-capable helpers; `collectSpriteRelsFromFrames` for preload |
| `tests/support/lab_replay_sprite_wire.py` | Deprecate harvest paint; migrate `sprite_paint_entries_for_frame` |
| `tests/support/lab_replay_paint_plan.py` | `sprite_rels_from_frame_index` Python mirror for preload tests |
| `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | Harvest quarantine contracts; no harvest in v2 paint paths |
| `tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py` | New: call-site audit + paint parity after migration |
| `tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py` | Update if golden used harvest helper |

---

## Task 1: Harvest audit + quarantine markers + v2 isolation tests

**Files:**
- Create: `tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (comments only)
- Modify: `tests/unit/asteroid_lab/test_lab_canvas_renderer.py`

- [ ] **Step 1: Write failing audit tests**

```python
# tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
LAB_JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_build_canvas_paint_plan_v2_branch_does_not_call_stage_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    fn = src.split("function buildCanvasPaintPlan(", 1)[1]
    v2_region = fn.split("labPaintV2Enabled()", 1)[1].split("const overlays = []", 1)[0]
    assert "stageCell" not in v2_region
    assert "collectFrameSpatialTargets" not in v2_region


def test_harvest_functions_marked_deprecated() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    for name in (
        "function collectFrameSpatialTargets(",
        "function labSpriteRelpathForCell(",
    ):
        idx = src.find(name)
        assert idx >= 0
        window = src[max(0, idx - 400) : idx]
        assert "HARVEST" in window or "deprecated" in window.lower() or "@deprecated" in window


def test_v2_dom_path_does_not_use_lab_sprite_relpath_for_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    render_body = src.split("function renderFullMapCells(", 1)[1].split(
        "function renderDiffOverlays(", 1
    )[0]
    assert "if (domPlan)" in render_body
    dom_block = render_body.split("if (domPlan)", 1)[1]
    next_legacy = dom_block.find("let tone = toneForFullMapCell")
    dom_v2 = dom_block[:next_legacy] if next_legacy >= 0 else dom_block[:1200]
    assert "labSpriteRelpathForCell" not in dom_v2
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py -v`

- [ ] **Step 3: Add quarantine banner comments** (no behavior change)

Above `collectFrameSpatialTargets`, `labSpriteRelpathForCell`, `frameCellIndexMap`, and legacy `stageCell`:

```javascript
  /** @deprecated HARVEST_PAINT — Slice 5 quarantine. Must not decide occupant/transport/candidate paint semantics. */
```

- [ ] **Step 4: Run audit tests — expect PASS** (adjust deprecated marker test if using `HARVEST_PAINT` string)

- [ ] **Step 5: Commit**

```bash
git add tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py \
  django_apps/web/static/web/js/asteroid_miner_layout_lab.js \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py
git commit -m "test(replay): Slice 5 harvest quarantine audit markers"
```

---

## Task 2: Migrate `frameCellIndexMap` to effective-view index (v2)

**Problem:** `resetDomCellsAtIndicesForFrame` uses `frameCellIndexMap` → harvest for token diff. Under v2, cell-at-index should come from merged view index, not flat overlay precedence.

**Files:**
- Modify: `lab_replay_paint_plan.js` — `buildCellByGridIndexFromFrame(frame, resolveCellIndex, options)`
- Modify: `asteroid_miner_layout_lab.js` — `frameCellIndexMap` delegates to paint-plan helper when v2

- [ ] **Step 1: Failing test**

```python
def test_js_build_cell_by_grid_index_from_frame_exists() -> None:
    src = (REPO / "django_apps/web/static/web/js/lab_replay_paint_plan.js").read_text(encoding="utf-8")
    assert "function buildCellByGridIndexFromFrame" in src
    assert "buildCellByGridIndexFromFrame:" in src
```

- [ ] **Step 2: Implement JS helper**

Build **once per frame**: effective index with carry → `Map<gridIdx, cellWireRow>` via `resolveCellIndex({x,y})`. Do not call `buildEffectiveCellViewIndex` per grid cell.

- [ ] **Step 3: Wire in `frameCellIndexMap`**

```javascript
  function frameCellIndexMap(frame, resolveCellIndex) {
    if (
      labPaintV2Enabled() &&
      typeof LabReplayPaintPlan.buildCellByGridIndexFromFrame === "function"
    ) {
      return LabReplayPaintPlan.buildCellByGridIndexFromFrame(
        frame,
        resolveCellIndex,
        labDomPaintOptionsFromContext(frame),
      );
    }
    // legacy harvest path unchanged until Task 5 delete
    ...
  }
```

- [ ] **Step 4: Contract test — v2 path does not call `collectFrameSpatialTargets` inside `frameCellIndexMap` when flag helper returns true** (static scan of v2 branch)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(replay): Slice 5 frameCellIndexMap effective-view migration (v2)"
```

---

## Task 3: Sprite preload + carry dedup → paint plan module

**Files:**
- Modify: `lab_replay_paint_plan.js`
- Modify: `asteroid_miner_layout_lab.js`

- [ ] **Step 1: Export `collectSpriteRelsFromPaintPlanFrames(frames, resolveCellIndex, options)`**

For each frame: `buildLabPaintPlanFromFrame` → collect unique `sprites[].rel`. No `labSpriteRelpathForCell`.

- [ ] **Step 2: Replace `collectSpriteRelpathsFromFrames` when v2**

```javascript
    function collectSpriteRelpathsFromFrames(framesArr) {
      if (
        labPaintV2Enabled() &&
        typeof LabReplayPaintPlan.collectSpriteRelsFromPaintPlanFrames === "function"
      ) {
        return LabReplayPaintPlan.collectSpriteRelsFromPaintPlanFrames(
          framesArr,
          resolveCellIndex,
          { replayFrames: framesArr, hasServerReplay: hasServerReplay },
        );
      }
      // legacy harvest until Task 5
      ...
    }
```

- [ ] **Step 3: Remove duplicate `frameHasSpriteCapableCells` / inner `lastFrameWithSpriteCapableCells` in canvas closure**

Use `LabReplayPaintPlan.indexHasSpriteCapableCells(buildEffectiveCellViewIndexWithCarry(...))` and exported `lastFrameWithSpriteCapableCells` from paint plan (already exists — wire canvas closure to module).

- [ ] **Step 4: Tests**

```python
def test_warmup_sprite_collect_uses_paint_plan_when_v2() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    body = src.split("function collectSpriteRelpathsFromFrames(", 1)[1][:700]
    assert "collectSpriteRelsFromPaintPlanFrames" in body
    assert "labPaintV2Enabled()" in body
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(replay): Slice 5 sprite preload and carry dedup via paint plan"
```

---

## Task 4: Python harvest paint migration

**Files:**
- Modify: `tests/support/lab_replay_sprite_wire.py`
- Modify: `tests/support/lab_replay_paint_plan.py`
- Modify: `tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py`

- [ ] **Step 1: Add `sprite_entries_from_paint_plan_frame(frame)` using `build_effective_cell_view_index` + `lab_paint_layers_from_view` + canvas adapter**

- [ ] **Step 2: Mark `sprite_paint_entries_for_frame` deprecated; delegate to new helper**

```python
def sprite_paint_entries_for_frame(frame: Mapping[str, object]) -> list[dict[str, object]]:
    """Deprecated harvest path — delegates to EffectiveCellView paint plan (Slice 5)."""
    return sprite_entries_from_paint_plan_frame(frame)
```

- [ ] **Step 3: Golden parity test — harvest vs paint plan agree on golden transport frames**

```python
def test_sprite_entries_paint_plan_matches_golden_transport_frame() -> None:
    for frame in golden_transport_replay_frames():
        harvest = _legacy_harvest_sprite_entries(frame)  # inline copy or git ref test
        planned = sprite_entries_from_paint_plan_frame(frame)
        assert sorted(planned, key=lambda r: (r["x"], r["y"])) == sorted(
            harvest, key=lambda r: (r["x"], r["y"])
        )
```

- [ ] **Step 4: Run golden + paint tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(replay): Slice 5 Python sprite entries via paint plan"
```

---

## Task 5: Legacy canvas harvest — quarantine completion (policy checkpoint)

**Precondition:** Tasks 1–4 green; manual smoke with `data-lab-paint-v2="1"` locally for frame 38 + golden solver replay.

**HITL checkpoint before implementation:** User picks policy **(A)** or **(B)**:

| Policy | Task 5 behavior | Task 6 |
|--------|-----------------|--------|
| **(A) Soft (default)** | Remove duplicate carry/preload harvest; v2 path exclusive; **keep** flag-off `stageCell` legacy branch | Delete legacy + NON_SPRITE + flag removal |
| **(B) Hard** | Remove `stageCell` + legacy harvest loop; `throw` or require v2 flag | Template default-on + symbol delete |

**Default for Subagent execution: (A)** — do not break flag-off production (template has no v2 flag today).

**Files:**
- Modify: `asteroid_miner_layout_lab.js`

- [ ] **Step 1: Audit test — v2 branch has no harvest**

```python
def test_build_canvas_paint_plan_v2_has_no_stage_cell() -> None:
    src = LAB_JS.read_text(encoding="utf-8")
    fn = src.split("function buildCanvasPaintPlan(", 1)[1]
    v2_region = fn.split("labPaintV2Enabled()", 1)[1]
    legacy_start = v2_region.find("const overlays = []")
    assert legacy_start >= 0
    assert "stageCell" not in v2_region[:legacy_start]
```

**Policy (A) — default Steps 2–4:**

- [ ] **Step 2:** Ensure early return to `buildLabPaintPlanFromFrame` when v2; legacy branch unchanged but marked `HARVEST_PAINT`
- [ ] **Step 3:** Add test `test_legacy_canvas_harvest_still_present_when_flag_off` — legacy `stageCell` exists until Task 6
- [ ] **Step 4: Commit** — `refactor(replay): Slice 5 v2-exclusive canvas paint; legacy harvest quarantined`

**Policy (B) — only on explicit user approval at checkpoint:**

- [ ] Remove `stageCell`, legacy harvest loop; require v2 or `data-lab-paint-legacy="1"`
- [ ] Commit — `refactor(replay): Slice 5 remove legacy canvas harvest paint branch`

**Slice 5 Tasks 1→5 do NOT touch:** legacy DOM `renderFullMapCells` branch, `NON_SPRITE`, template flag default.

---

## Task 6 (HITL delete subtask): Harvest delete + legacy DOM + NON_SPRITE cleanup

**Only after Task 5 gate + explicit user approval.**

**Includes Slice 4 Task 7:** `NON_SPRITE_OVERLAY_CELL_KINDS.candidate_miner` removal.

- [ ] Delete legacy `buildCanvasPaintPlan` harvest branch (`stageCell`, harvest loops)
- [ ] Migrate or remove legacy DOM harvest in `renderFullMapCells` when flag off
- [ ] Remove `candidate_miner` from `NON_SPRITE_OVERLAY_CELL_KINDS` (JS + `lab_replay_sprite_wire.py`)
- [ ] Delete `labSpriteRelpathForCell` when no callers remain
- [ ] Rename/retain `collectFrameSpatialCoordsForLayout` for `computeReplayGridLayout` bbox only
- [ ] Template: default `data-lab-paint-v2="1"` (separate HITL) or remove flag entirely

---

## Task 7: Validation gate + epic acceptance

- [ ] **Full matrix**

```bash
python -m pytest \
  tests/unit/asteroid_lab/replay/test_lab_replay_harvest_quarantine.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_dom_adapter.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_plan.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_golden.py \
  tests/unit/asteroid_lab/replay/test_lab_replay_paint_canvas_adapter.py \
  tests/unit/asteroid_lab/replay/test_replay_wire_read_sanitize.py \
  tests/unit/asteroid_lab/replay/test_replay_frame_cell_resolver.py \
  tests/unit/asteroid_lab/test_lab_canvas_renderer.py \
  tests/unit/asteroid_lab/test_lab_renderer_token_diff.py \
  tests/unit/asteroid_lab/test_shape_belt_ui_wire_ban.py \
  -q
```

Expected: all passed

- [ ] **Manual smoke:** v2 on (or v2-only after Task 6) — frame 38 `(10,7)`, golden transport replay, flag-off behavior per chosen Task 5 policy

- [ ] **Kanban:** epic acceptance ticks; archive when §3 epic acceptance met

- [ ] **Optional milestone tag (user command only):**

```bash
git tag -a replay-sprite-visibility-v1 -m "Replay paint v2: harvest removed, epic complete"
```

---

## Out of scope (Slice 5)

- Playwright blur PNG regression
- Server-side paint plan API
- Task 7 Slice 4 before Task 6 here
- Auto `git push` of tags

---

## Self-review

| Spec § | Task |
|--------|------|
| §2.1 harvest must not decide semantics | Tasks 1–5 |
| §2.7 quarantine then delete | Tasks 1, 5, 6 |
| §3.3 Slice 5 stop | Task 7 |
| §3.4 rollback until delete | Task 5/6 HITL |
| Slice 4 Task 7 NON_SPRITE | Task 6 HITL only |

---

## Execution handoff

**Plan saved:** `docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-5.md`

**Do not execute until plan review approved.**

**Plan review:** APPROVED WITH AMENDMENTS (2026-06-12). Tasks 1→5 executable; Task 6/7 HITL.

After approval: **Subagent-Driven**, Tasks 1→5 with **Task 5 policy (A) default**; **Task 6 HITL**; **Task 7** epic gate after Task 6 or after Task 5 if policy (A) only.
