# Sequence 3B-R — Unified RTTP Algorithm Replay Frames Implementation Plan

> **SUPERSEDED (product behavior):** [Sequence 3B-S full-snapshot interleaved replay](../specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md). `inherited_snapshot` tail append is obsolete. ORM `:rttp` write buffer remains. Implementation: [2026-05-23-sequence-3b-s-rttp-full-snapshot-replay.md](2026-05-23-sequence-3b-s-rttp-full-snapshot-replay.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Append RTTP algorithm milestone frames into the single Lab product timeline (`lab_replay_frames_json`) so one scrubber advances through map frames then algorithm frames, using `render_mode: inherited_snapshot` when no map payload exists.

**Architecture:** Keep DB persistence on `{run_key}:rttp` (PR #43). Change **compose only**: `build_lab_replay_frames_for_project` still builds map timeline from inspection + runtime segments, then appends algorithm frames from `build_lab_optimization_milestone_frames_for_project`, renumbers `frame_index` to `0..N-1`, and adds `render_mode` / `base_frame_index`. Lab JS keeps one `replayFrames` array; `renderReplayFrame` holds the last renderable map when `render_mode === "inherited_snapshot"`. `lab_optimization_milestone_frames_json` stays **diagnostic-only** (API compat), not a UI primary path.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`), vanilla JS (`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`).

**Supersedes:** [`2026-05-23-sequence-3b-optimization-replay-lab-timeline.md`](2026-05-23-sequence-3b-optimization-replay-lab-timeline.md) PR-2 “Section B panel” approach (Approach B). PR #43 backend adapter remains; **primary Lab surface moves to unified append**.

**Related:** [`rollback_baseline_lab_replay_timeline.md`](../../documents/plans/asteroid_lab_optimization/rollback_baseline_lab_replay_timeline.md) · [`2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md`](../specs/2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md) (amend in PR-3)

---

## Contract delta (3B → 3B-R)

| Topic | 3B v0 (superseded UI) | 3B-R (new) |
|-------|------------------------|------------|
| Primary Lab timeline | `lab_replay_frames_json` = map only | `lab_replay_frames_json` = map + algorithm tail |
| H1 | `lab_event_types ∩ RTTP = ∅` | RTTP types allowed **at tail**; map-only prefix unchanged |
| UI | Separate Optimization Milestones panel | **Single scrubber**; panel removed/hidden |
| RTTP frame map | No `map_view` (Section B) | `render_mode: inherited_snapshot` + `base_frame_index` |
| ORM `:rttp` track | Unchanged | Unchanged (source for append) |
| Solver reads replay | Forbidden | Forbidden (unchanged) |

### New invariants (H1-R)

```text
lab_replay_frames_json may include RTTP_MILESTONE_EVENT_TYPES at the tail.

Every algorithm frame must:
  - render_mode == "inherited_snapshot"
  - base_frame_index points to last renderable map frame (global index)
  - no full_map / non-empty map_view / non-empty cell_overlay_json on the frame body
  - inspector.kind == "optimization_milestone" (or equivalent stable key)

frame_index is continuous 0 .. lab_replay_frame_count - 1.

Replay remains output-only: optimization/ must not import replay read adapters or ReplayFrame ORM.
```

### Wire example (Run Solver / SSR)

```json
{
  "lab_replay_frame_count": 26,
  "lab_replay_frames_json": [
    { "frame_index": 0, "event_type": "decode.started", "map_view": { "full_cells": [] } },
    { "frame_index": 21, "event_type": "reconstruction.completed", "map_view": { "full_cells": [] } },
    {
      "frame_index": 22,
      "event_type": "routing.probe_started",
      "phase": "rttp_pipeline",
      "title": "RTTP pipeline started",
      "render_mode": "inherited_snapshot",
      "base_frame_index": 21,
      "map_view": { "full_cells": [], "cell_delta": [], "overlay_cells": [], "bbox": { "min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0 } },
      "inspector": { "kind": "optimization_milestone" },
      "metrics": { "skeleton_id": "…" }
    }
  ],
  "lab_optimization_milestone_frames_json": [],
  "lab_optimization_milestone_frame_count": 0
}
```

`lab_optimization_milestone_frames_json` may still mirror raw milestone rows for debug in PR-1 compat PR; UI must not read it after PR-2.

---

## File map

| File | PR | Responsibility |
|------|-----|----------------|
| `django_apps/asteroid_lab/replay/replay_render_modes.py` | 1 | `RENDER_MODE_INHERITED_SNAPSHOT` const |
| `django_apps/asteroid_lab/services/lab_unified_replay_append.py` | 1 | Append + reindex + inherited_snapshot enrichment |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | 1 | Call append after compose |
| `django_apps/asteroid_lab/services/lab_optimization_milestone_payload.py` | 1 | Unchanged read source (optional: export helper for phase→ReplayPhase) |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | 1 | `lab_replay_frame_count` reflects unified length |
| `django_apps/web/views/public_pages.py` | 1 | Bundle uses unified `lab_replay_frames_json` only for scrubber |
| `django_apps/web/services/asteroid_lab_page_context.py` | 1 | SSR unified frames |
| `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` | 1 | Append + invariants unit tests |
| `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py` | 1 | Replace H1 disjoint with H1-R tail assertions |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | 1 | Unified count ≥ map-only + 4 |
| `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` | 1 | Extend: no `lab_unified_replay_append` in optimization/ |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | 2 | `inherited_snapshot` render + drop panel primary path |
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | 2 | Remove or hide milestones panel + optional diagnostic script only |
| `tests/unit/web/test_asteroid_lab_page_context.py` | 2 | JS smoke: inherited_snapshot; no separate panel primary |
| `docs/superpowers/specs/2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md` | 3 | Amendment: Approach C / unified |
| `docs/superpowers/plans/2026-05-23-sequence-3b-optimization-replay-lab-timeline.md` | 3 | Superseded banner at top |
| `documents/plans/asteroid_lab_optimization/rollback_baseline_lab_replay_timeline.md` | 3 | Cross-link 3B-R |

---

## PR-1 — Backend unified replay append

### Task 1: Render mode constant + append module skeleton

**Files:**
- Create: `django_apps/asteroid_lab/replay/replay_render_modes.py`
- Create: `django_apps/asteroid_lab/services/lab_unified_replay_append.py`
- Create: `tests/unit/asteroid_lab/test_lab_unified_replay_append.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_lab_unified_replay_append.py
from __future__ import annotations

from django_apps.asteroid_lab.replay.replay_render_modes import RENDER_MODE_INHERITED_SNAPSHOT
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.lab_unified_replay_append import (
    append_algorithm_frames_to_unified_lab_replay,
    last_renderable_map_frame_index,
)


def _map_frame(idx: int) -> dict:
    return {
        "frame_index": idx,
        "event_type": "reconstruction.completed",
        "phase": "reconstruction",
        "title": "Map",
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "cell_delta": [],
            "overlay_cells": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "inspector": {},
        "metrics": {},
    }


def test_last_renderable_map_frame_index_picks_last_with_cells() -> None:
    frames = [_map_frame(0), {"frame_index": 1, "event_type": "decode.started", "map_view": {}}]
    assert last_renderable_map_frame_index(frames) == 0


def test_append_renumbers_and_adds_inherited_snapshot_tail() -> None:
    map_frames = [_map_frame(0), _map_frame(1)]
    milestones = [
        {
            "frame_index": 0,
            "phase": "rttp_pipeline",
            "event_type": "routing.probe_started",
            "title": "RTTP pipeline started",
            "description": "",
            "inspector": {},
            "metrics": {"k": 1},
        },
        {
            "frame_index": 1,
            "phase": "candidate_generation",
            "event_type": "candidate.generated",
            "title": "Candidates",
            "description": "",
            "inspector": {},
            "metrics": {},
        },
    ]
    out = append_algorithm_frames_to_unified_lab_replay(map_frames, milestones)
    assert len(out) == 4
    assert [f["frame_index"] for f in out] == [0, 1, 2, 3]
    tail = out[2:]
    assert {f["event_type"] for f in tail} <= RTTP_MILESTONE_EVENT_TYPES
    for fr in tail:
        assert fr["render_mode"] == RENDER_MODE_INHERITED_SNAPSHOT
        assert fr["base_frame_index"] == 1
        assert fr["inspector"]["kind"] == "optimization_milestone"
        assert "full_map" not in fr
        assert not fr.get("map_view", {}).get("full_cells")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_unified_replay_append.py -v`  
Expected: FAIL — `ModuleNotFoundError` for `lab_unified_replay_append`

- [ ] **Step 3: Implement minimal module**

```python
# django_apps/asteroid_lab/replay/replay_render_modes.py
RENDER_MODE_INHERITED_SNAPSHOT = "inherited_snapshot"

__all__ = ["RENDER_MODE_INHERITED_SNAPSHOT"]
```

```python
# django_apps/asteroid_lab/services/lab_unified_replay_append.py
"""Append RTTP algorithm milestone dicts onto unified lab_replay_frames_json (output-only)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.replay.replay_render_modes import RENDER_MODE_INHERITED_SNAPSHOT

INSPECTOR_KIND_OPTIMIZATION_MILESTONE = "optimization_milestone"

_EMPTY_MAP_VIEW: dict[str, Any] = {
    "base_ref": None,
    "full_cells": [],
    "cell_delta": [],
    "overlay_cells": [],
    "annotations": [],
    "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
}


def _frame_has_renderable_map_cells(frame: dict[str, Any]) -> bool:
    mv = frame.get("map_view")
    if not isinstance(mv, dict):
        return False
    full_cells = mv.get("full_cells")
    if isinstance(full_cells, list) and len(full_cells) > 0:
        return True
    cell_delta = mv.get("cell_delta")
    if isinstance(cell_delta, list) and len(cell_delta) > 0:
        return True
    overlay = mv.get("overlay_cells")
    return isinstance(overlay, list) and len(overlay) > 0


def last_renderable_map_frame_index(map_frames: list[dict[str, Any]]) -> int:
    for idx in range(len(map_frames) - 1, -1, -1):
        if _frame_has_renderable_map_cells(map_frames[idx]):
            return idx
    return max(0, len(map_frames) - 1)


def _algorithm_frame_from_milestone(
    milestone: dict[str, Any],
    *,
    base_frame_index: int,
) -> dict[str, Any]:
    inspector = dict(milestone.get("inspector") or {})
    inspector.setdefault("kind", INSPECTOR_KIND_OPTIMIZATION_MILESTONE)
    return {
        "frame_index": 0,
        "phase": str(milestone.get("phase") or ""),
        "event_type": str(milestone.get("event_type") or ""),
        "title": str(milestone.get("title") or ""),
        "description": str(milestone.get("description") or ""),
        "render_mode": RENDER_MODE_INHERITED_SNAPSHOT,
        "base_frame_index": int(base_frame_index),
        "map_view": dict(_EMPTY_MAP_VIEW),
        "inspector": inspector,
        "metrics": dict(milestone.get("metrics") or {}),
    }


def append_algorithm_frames_to_unified_lab_replay(
    map_frames: list[dict[str, Any]],
    algorithm_milestones: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unified: list[dict[str, Any]] = [dict(fr) for fr in map_frames]
    if not algorithm_milestones:
        for i, fr in enumerate(unified):
            fr["frame_index"] = i
        return unified
    base_idx = last_renderable_map_frame_index(unified)
    for m in algorithm_milestones:
        unified.append(_algorithm_frame_from_milestone(m, base_frame_index=base_idx))
    for i, fr in enumerate(unified):
        fr["frame_index"] = i
    return unified


__all__ = [
    "append_algorithm_frames_to_unified_lab_replay",
    "last_renderable_map_frame_index",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_unified_replay_append.py -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/replay/replay_render_modes.py django_apps/asteroid_lab/services/lab_unified_replay_append.py tests/unit/asteroid_lab/test_lab_unified_replay_append.py`

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/replay/replay_render_modes.py django_apps/asteroid_lab/services/lab_unified_replay_append.py tests/unit/asteroid_lab/test_lab_unified_replay_append.py
git commit -m "feat(lab-replay): unified append module for RTTP algorithm frames"
```

---

### Task 2: Wire `build_lab_replay_frames_for_project`

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Test: `tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py` (extend or add `test_build_lab_replay_includes_rttp_tail_when_milestones_exist`)

- [ ] **Step 1: Add failing integration-style unit test**

Add to `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` or new test file that mocks milestone builder — prefer **DB integration** extension in Task 3. For payload wiring, add:

```python
# tests/unit/asteroid_lab/test_lab_replay_timeline_unified_append.py (new file)
@pytest.mark.django_db
def test_build_lab_replay_frames_appends_rttp_tail_when_track_exists(...):
    ...
```

Use same fixture pattern as `test_lab_json_bundle_uses_latest_solver_run_for_section_b_v0` in `tests/unit/web/test_asteroid_lab_page_context.py`: inspection track + `:rttp` track with 4 milestone events → `build_lab_replay_frames_for_project` returns count == map_count + 4, tail event types ⊇ RTTP_MILESTONE_EVENT_TYPES.

- [ ] **Step 2: Run test — expect FAIL** (map-only length)

- [ ] **Step 3: Patch `build_lab_replay_frames_for_project`**

```python
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_unified_replay_append import (
    append_algorithm_frames_to_unified_lab_replay,
)

def build_lab_replay_frames_for_project(
    project_id: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lab_frames = _lab_timeline_frames_for_project(int(project_id))
    runtime_frames = _solver_runtime_timeline_frames_for_project(int(project_id))
    combined = compose_replay_timeline(
        lab_frames=(*lab_frames, *runtime_frames),
        max_frames=replay_limits.MAX_LAB_REPLAY_TIMELINE_FRAMES,
    )
    serialized = [replay_timeline_frame_to_json_dict(fr) for fr in combined]
    milestone_frames, _milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(project_id),
        run_key=None,
    )
    serialized = append_algorithm_frames_to_unified_lab_replay(serialized, milestone_frames)
    diagnostic = _lab_replay_diagnostic_reason(int(project_id), composed_count=len(serialized))
    metrics = _track_metrics_from_serialized_frames(serialized, diagnostic_reason=diagnostic)
    return serialized, metrics
```

- [ ] **Step 4: Run narrow tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_unified_replay_append.py tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(lab-replay): append RTTP milestones into lab_replay_frames_json"
```

---

### Task 3: Replace H1 integration test (disjoint → tail)

**Files:**
- Modify: `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

- [ ] **Step 1: Replace `test_run_solver_lab_json_uses_inspection_not_rttp_optimization_track` body**

Rename to `test_run_solver_lab_json_unified_replay_includes_rttp_at_tail` and assert:

```python
body = entry_result_to_json_dict(result)
frames = body["lab_replay_frames_json"]
map_types = {fr["event_type"] for fr in frames[: -len(milestones)]}  # or split by first inherited_snapshot index
assert map_types.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)
tail = [fr for fr in frames if fr.get("render_mode") == "inherited_snapshot"]
assert len(tail) >= 4
assert RTTP_MILESTONE_EVENT_TYPES <= {fr["event_type"] for fr in tail}
assert body["lab_replay_frame_count"] == len(frames)
```

Keep assertions that `:rttp` ORM track exists and is not the inspection track used for **map-only** segment (still exclude `:rttp` from `get_latest_lab_replay_track_for_project`).

- [ ] **Step 2: Run integration test**

Run: `python -m pytest tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py -v`

- [ ] **Step 3: Commit**

```bash
git commit -m "test(lab-replay): H1-R unified tail instead of disjoint lab JSON"
```

---

### Task 4: Import boundary + PR gate

- [ ] **Step 1: Extend `test_optimization_milestone_import_boundary.py`**

```python
for needle in ("lab_optimization_milestone_payload", "lab_unified_replay_append", "lab_replay_timeline_payload"):
    ...
```

- [ ] **Step 2: Full narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_unified_replay_append.py tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py -v
python -m ruff check django_apps/asteroid_lab/services/lab_unified_replay_append.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
```

- [ ] **Step 3: Commit if fixes only**

---

## PR-2 — JS `inherited_snapshot` + remove panel primary path

### Task 5: Revert / supersede separate milestones panel

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Modify: `tests/unit/web/test_asteroid_lab_page_context.py`

- [ ] **Step 1: Update JS smoke tests first (red)**

Remove assertions that require separate panel as primary:

```python
# Remove or invert:
# assert "renderOptimizationMilestonesPanel" in js
# assert "lab-optimization-milestone-frames-data" in js as primary reader

# Add:
assert "inherited_snapshot" in js
assert "RENDER_MODE_INHERITED_SNAPSHOT" in js or 'render_mode' in js and "inherited_snapshot" in js
assert "lastRenderableReplayFrame" in js or "inheritedSnapshot" in js
```

Remove `test_lab_solver_template_includes_optimization_milestones_empty_copy` **or** change to assert panel is **hidden** (`hidden` class on panel wrapper).

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/web/test_asteroid_lab_page_context.py::test_lab_js_replay_wiring_smoke -v`

- [ ] **Step 3: Implement JS**

In `asteroid_miner_layout_lab.js`:

1. Remove read of `lab-optimization-milestone-frames-data` at init (or keep read-only for debug log only).
2. Remove `renderOptimizationMilestonesPanel` calls from `replaceLabReplayPayload`.
3. Add module-level or closure state:

```javascript
let lastRenderableReplayFrame = null;

function frameHasRenderableMap(frame) {
  return fullMapCellsFromFrame(frame).length > 0;
}

function renderReplayFrame(frame, baseClasses, domCells, resolveCellIndex) {
  if (
    frame &&
    frame.render_mode === "inherited_snapshot" &&
    lastRenderableReplayFrame &&
    frameHasRenderableMap(lastRenderableReplayFrame)
  ) {
    renderReplayFrame(lastRenderableReplayFrame, baseClasses, domCells, resolveCellIndex);
    updateAlgorithmInspectorFromFrame(frame);
    return;
  }
  resetGridBase(domCells, baseClasses);
  if (!frame || typeof frame !== "object") return;
  const fm = fullMapCellsFromFrame(frame);
  if (fm.length) {
    lastRenderableReplayFrame = frame;
    // ... existing full map path ...
    return;
  }
  // ... overlay-only path; do not clear lastRenderableReplayFrame ...
}
```

Extract title/event/description/metrics HUD update into `updateAlgorithmInspectorFromFrame(frame)` reusing existing `updateFrameInfo` fields.

4. On `replaceLabReplayPayload`, only assign `replayFrames = payload.lab_replay_frames_json` (drop milestone side channel).

- [ ] **Step 4: Template — hide panel**

Wrap `#lab-optimization-milestones-panel` in `class="hidden"` or delete block; keep `lab-optimization-milestone-frames-data` json_script only if diagnostic API still returns it.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/unit/web/test_asteroid_lab_page_context.py -v`

- [ ] **Step 6: Manual smoke**

Run Solver → scrubber shows **26 / 26** (example: 22 map + 4 algorithm). Frames 23–26 show RTTP titles; map stays on last reconstruction.

- [ ] **Step 7: Commit**

```bash
git commit -m "feat(lab-ui): unified replay scrubber with inherited_snapshot RTTP frames"
```

---

## PR-3 — Docs + plan supersede

### Task 6: Amend spec and supersede old plan

**Files:**
- Modify: `docs/superpowers/specs/2026-05-23-sequence-3b-optimization-replay-lab-timeline-design.md`
- Modify: `docs/superpowers/plans/2026-05-23-sequence-3b-optimization-replay-lab-timeline.md`

- [x] **Step 1:** Add top banner to old plan: **SUPERSEDED by 3B-R** with link.
- [x] **Step 2:** Add spec amendment section **3B-R unified inherited_snapshot** — Approach B panel marked superseded; Approach C adopted.
- [x] **Step 3:** Commit `docs: sequence 3B-R unified replay contract`

---

## PR split / branch strategy

```text
Branch feat/sequence-3b-r-unified-rttp-replay (from master after #43 merge)

PR-1: backend append + H1-R tests  (can ship first)
PR-2: JS inherited_snapshot + hide panel  (depends on PR-1)
PR-3: docs only  (can merge with PR-2)
```

If `feat/sequence-3b-optimization-milestones-ui` branch exists: **abandon or rebase** — drop panel commits; cherry-pick only tests/docs if useful.

---

## Forbidden shortcuts (unchanged)

- Do not append milestones by mutating `lab_replay_frames_json` inside optimization solver code.
- Do not use `innerHTML` for replay strings in JS.
- Do not add `full_map` / dense `map_view` to RTTP frames to “fix” render.
- Do not delete H1 test without H1-R replacement.
- Do not weaken `test_optimization_milestone_import_boundary`.

---

## Self-review (plan author)

| Check | Status |
|-------|--------|
| Spec coverage: single scrubber 26/26 | Task 5–6 manual + integration |
| Spec coverage: inherited_snapshot | Task 1 + 5 |
| Spec coverage: output-only import boundary | Task 4 |
| Spec coverage: diagnostic Section B optional | Wire note in Task 2; keep in API |
| Placeholder scan | No TBD |
| `ReplayTimelineFrame` enum gap (`ga.best_updated`, `routing.probe_started`) | Bypassed by post-serialize dict append (no `replay_timeline_frame_from_json_dict` on tail) |

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, two-stage review (spec then quality). Use superpowers:subagent-driven-development.

2. **Inline Execution** — this session with superpowers:executing-plans and checkpoints after PR-1 / PR-2.

**Which approach?**

Also confirm branch handling: abandon current `feat/sequence-3b-optimization-milestones-ui` panel work and open `feat/sequence-3b-r-unified-rttp-replay` from `master`.

---

## Implementation status

**Branch:** `feat/sequence-3b-r-unified-rttp-replay`

| Task | Status |
|------|--------|
| Task 1: Render mode constant + append module skeleton | Complete |
| Task 2: Wire `build_lab_replay_frames_for_project` | Complete |
| Task 3: Replace H1 integration test (disjoint → tail) | Complete |
| Task 4: Import boundary + PR gate | Complete |
| Task 5: JS `inherited_snapshot` + remove panel primary path | Complete |
| Task 6: Docs + plan supersede | Complete (this commit) |

### Commits (`master..HEAD`)

```text
f67404f9 feat(lab-ui): unified replay scrubber with inherited_snapshot RTTP frames
5f7ca2ea test(lab-replay): extend optimization import boundary for unified replay
bd6e8ac3 test(lab-replay): H1-R unified tail instead of disjoint lab JSON
22550bad feat(lab-replay): append RTTP milestones into lab_replay_frames_json
6cecb451 feat(lab-replay): unified append module for RTTP algorithm frames
```
