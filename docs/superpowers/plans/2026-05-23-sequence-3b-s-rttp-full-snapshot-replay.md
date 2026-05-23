# Sequence 3B-S — RTTP Full-Snapshot Interleaved Lab Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project `:rttp` write-buffer rows into `lab_replay_frames_json` as interleaved full `map_view` snapshot frames (no `inherited_snapshot`), on the single Lab scrubber timeline.

**Architecture:** Product-single, storage-dual transitional model per [design spec](../specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md). `build_lab_replay_frames_for_project` composes lab + runtime frames, then `interleave_rttp_snapshot_frames` inserts projected RTTP frames at anchor indices and renumbers `frame_index`. PR-1 copies `full_cells` from nearest prior renderable frame at compose time; overlays from `:rttp` `cell_overlay_json` when non-empty. `optimization/` recording unchanged for G8.

**Tech Stack:** Python 3.12+, Django 5.2, pytest, ruff, mypy (`django_apps config src`), vanilla JS (`django_apps/web/static/web/js/asteroid_miner_layout_lab.js`).

**Spec:** [2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md](../specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md)

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md` | exists | Canonical contract |
| `docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md` | modify | SUPERSEDED banner → 3B-S |
| `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py` | create | Anchor resolve, project row, interleave |
| `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py` | modify | Call interleave; stop tail inherited append |
| `django_apps/asteroid_lab/services/lab_unified_replay_append.py` | modify/deprecate | Remove product RTTP path or re-export shims |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | modify | Remove inherited_snapshot render branch |
| `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py` | create | Compose unit tests |
| `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` | modify | Delete/replace inherited_snapshot tests |
| `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py` | modify | H1-R → H1-S |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | modify | H1-S assertions |
| `tests/unit/web/test_asteroid_lab_page_context.py` | modify | `test_rttp_track_not_exposed_as_product_timeline`; JS smoke |
| `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` | modify | Allow `lab_rttp_snapshot_compose` in compose layer only |

---

## Task 0: Supersede 3B-R in docs

**Files:**
- Modify: `docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md` (top banner only)

- [ ] **Step 1: Add banner after title**

```markdown
> **SUPERSEDED (product behavior):** [Sequence 3B-S full-snapshot interleaved replay](2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md). `inherited_snapshot` tail append is obsolete. ORM `:rttp` write buffer remains.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/plans/2026-05-23-sequence-3b-r-unified-rttp-replay.md docs/superpowers/specs/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay-design.md
git commit -m "docs: 3B-S RTTP full-snapshot replay spec; supersede 3B-R product path"
```

---

## Task 1: `lab_rttp_snapshot_compose` module

**Files:**
- Create: `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py`
- Create: `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py
from __future__ import annotations

from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.lab_rttp_snapshot_compose import (
    frame_has_renderable_map,
    interleave_rttp_snapshot_frames,
    last_renderable_frame_index,
    project_rttp_row_to_product_frame,
)


def _map_frame(idx: int, event_type: str = "reconstruction.completed") -> dict:
    return {
        "frame_index": idx,
        "event_type": event_type,
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


def test_frame_has_renderable_map_cells() -> None:
    assert frame_has_renderable_map(_map_frame(0)) is True
    assert frame_has_renderable_map({"event_type": "x", "map_view": {}}) is False


def test_project_rttp_row_has_concrete_full_cells_no_inherited_mode() -> None:
    base = _map_frame(0)
    row = {
        "event_type": "routing.probe_started",
        "phase": "rttp_pipeline",
        "title": "RTTP pipeline started",
        "description": "probe domain snapshot",
        "metrics": {"skeleton_id": "sk1"},
        "cell_overlay_json": {"cells": [{"x": 1, "y": 0, "kind": "probe.path"}]},
    }
    out = project_rttp_row_to_product_frame(row, base_map_view=dict(base["map_view"]))
    assert out.get("render_mode") != "inherited_snapshot"
    assert "render_mode" not in out
    assert len(out["map_view"]["full_cells"]) >= 1
    assert out["description"] == "probe domain snapshot"


def test_interleave_inserts_after_renderable_not_tail_only() -> None:
    map_frames = [_map_frame(0), _map_frame(1)]
    rows = [
        {
            "event_type": "routing.probe_started",
            "phase": "rttp_pipeline",
            "title": "RTTP started",
            "description": "",
            "metrics": {},
            "cell_overlay_json": {},
        },
        {
            "event_type": "candidate.generated",
            "phase": "candidate_generation",
            "title": "Candidates",
            "description": "",
            "metrics": {},
            "cell_overlay_json": {},
        },
    ]
    out = interleave_rttp_snapshot_frames(map_frames, rows)
    assert len(out) == 4
    assert [f["frame_index"] for f in out] == [0, 1, 2, 3]
    rttp_idxs = [i for i, f in enumerate(out) if f["event_type"] in RTTP_MILESTONE_EVENT_TYPES]
    assert rttp_idxs == [2, 3]
    assert rttp_idxs[0] < len(out) - 1
    for fr in out:
        assert fr.get("render_mode") != "inherited_snapshot"
        if fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES:
            assert len(fr["map_view"]["full_cells"]) >= 1


def test_last_renderable_prefers_candidate_generated_over_decode() -> None:
    frames = [
        _map_frame(0, "decode.started"),
        _map_frame(1, "candidate.generated"),
    ]
    assert last_renderable_frame_index(frames) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -v`  
Expected: FAIL — `ModuleNotFoundError: lab_rttp_snapshot_compose`

- [ ] **Step 3: Implement module**

```python
# django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py
"""Project :rttp write-buffer rows into full-snapshot Lab replay frames (output-only)."""

from __future__ import annotations

import copy
from typing import Any

from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)

_RECONSTRUCTION_COMPLETED = "reconstruction.completed"


def frame_has_renderable_map(frame: dict[str, Any]) -> bool:
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


def last_renderable_frame_index(frames: list[dict[str, Any]]) -> int:
    for idx in range(len(frames) - 1, -1, -1):
        if frame_has_renderable_map(frames[idx]):
            return idx
    return max(0, len(frames) - 1)


def _find_reconstruction_completed_index(frames: list[dict[str, Any]]) -> int | None:
    for idx in range(len(frames) - 1, -1, -1):
        if str(frames[idx].get("event_type") or "") == _RECONSTRUCTION_COMPLETED:
            if frame_has_renderable_map(frames[idx]):
                return idx
    return None


def resolve_insert_index(base_frames: list[dict[str, Any]]) -> int:
    """Anchor: last renderable; fallback reconstruction.completed; fallback last renderable."""
    if not base_frames:
        return 0
    recon = _find_reconstruction_completed_index(base_frames)
    if recon is not None:
        return recon
    return last_renderable_frame_index(base_frames)


def _overlay_cells_from_cell_overlay_json(overlay: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(overlay, dict):
        return []
    cells = overlay.get("cells")
    if isinstance(cells, list):
        return [dict(c) for c in cells if isinstance(c, dict)]
    return []


def project_rttp_row_to_product_frame(
    row: dict[str, Any],
    *,
    base_map_view: dict[str, Any],
) -> dict[str, Any]:
    mv = copy.deepcopy(base_map_view)
    overlay_from_row = _overlay_cells_from_cell_overlay_json(
        row.get("cell_overlay_json") if isinstance(row.get("cell_overlay_json"), dict) else None
    )
    if overlay_from_row:
        mv["overlay_cells"] = overlay_from_row
    else:
        mv.setdefault("overlay_cells", [])
    return {
        "frame_index": 0,
        "phase": str(row.get("phase") or ""),
        "event_type": str(row.get("event_type") or ""),
        "title": str(row.get("title") or ""),
        "description": str(row.get("description") or ""),
        "map_view": mv,
        "inspector": dict(row.get("inspector") or {}),
        "metrics": dict(row.get("metrics") or {}),
    }


def interleave_rttp_snapshot_frames(
    base_frames: list[dict[str, Any]],
    rttp_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    unified: list[dict[str, Any]] = [copy.deepcopy(fr) for fr in base_frames]
    if not rttp_rows:
        for i, fr in enumerate(unified):
            fr["frame_index"] = i
        return unified

    insert_at = resolve_insert_index(unified)
    base_mv = dict(unified[insert_at].get("map_view") or {})
    projected: list[dict[str, Any]] = []
    for row in rttp_rows:
        if str(row.get("event_type") or "") not in RTTP_MILESTONE_EVENT_TYPES:
            continue
        projected.append(project_rttp_row_to_product_frame(row, base_map_view=base_mv))

    # Insert block after anchor (interleaved block; monotonic row order preserved)
    unified[insert_at + 1 : insert_at + 1] = projected
    for i, fr in enumerate(unified):
        fr["frame_index"] = i
    return unified


__all__ = [
    "frame_has_renderable_map",
    "interleave_rttp_snapshot_frames",
    "last_renderable_frame_index",
    "project_rttp_row_to_product_frame",
    "resolve_insert_index",
]
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py -v`  
Expected: PASS

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py`

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py
git commit -m "feat(lab-replay): RTTP full-snapshot compose projection module"
```

---

## Task 2: Load `:rttp` rows and wire `build_lab_replay_frames_for_project`

**Files:**
- Modify: `django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py` (add `load_rttp_compose_rows_for_project`)
- Modify: `django_apps/asteroid_lab/services/lab_replay_timeline_payload.py`
- Test: extend `tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py` or `test_lab_rttp_snapshot_compose.py`

- [ ] **Step 1: Add loader + failing DB test**

```python
# In lab_rttp_snapshot_compose.py — add after imports:
from django_apps.asteroid_lab.models import ReplayFrame, ReplayTrack, SolverRun
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key


def load_rttp_compose_rows_for_project(project_id: int, *, run_key: str | None = None) -> list[dict[str, Any]]:
    """Read :rttp ORM rows for compose (write buffer; not product timeline)."""
    qs = SolverRun.objects.filter(project_id=int(project_id)).order_by("-id")
    if run_key is not None:
        qs = qs.filter(run_key=str(run_key))
    run = qs.first()
    if run is None:
        return []
    track = ReplayTrack.objects.filter(
        project_id=int(project_id),
        track_key=rttp_optimization_track_key(str(run.run_key)),
    ).first()
    if track is None:
        return []
    rows: list[dict[str, Any]] = []
    for frame in ReplayFrame.objects.filter(replay_track_id=track.id).order_by("frame_index"):
        payload = dict(frame.frame_payload or {})
        rows.append(
            {
                "event_type": str(payload.get("event_type") or ""),
                "phase": str(frame.phase),
                "title": str(frame.title),
                "description": str(frame.description or ""),
                "metrics": dict(frame.metric_snapshot_json or {}),
                "cell_overlay_json": dict(frame.cell_overlay_json or {}),
                "inspector": {},
            }
        )
    return rows
```

```python
# tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py — add:
import pytest
from django.test import override_settings
from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import build_lab_replay_frames_for_project
from django_apps.asteroid_lab.services.replay_pipeline_service import build_initial_replay_for_map_input
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project

# reuse _minimal_valid_copy from test_rttp_runtime_replay_db or inline minimal copy helper


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_build_lab_replay_has_no_inherited_snapshot_when_rttp_track_exists(minimal_copy) -> None:
    proj = m.AsteroidProject.objects.create(name="3bs", slug="3bs-compose")
    inp = create_copy_code_map_input(proj, minimal_copy)
    build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
    run_solver_runtime_for_project(int(proj.pk), run_key="3bs", config={"rttp_record_replay": True})
    frames, _ = build_lab_replay_frames_for_project(int(proj.pk))
    assert frames
    assert all(fr.get("render_mode") != "inherited_snapshot" for fr in frames)
    rttp = [fr for fr in frames if fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES]
    assert len(rttp) >= 4
    for fr in rttp:
        assert len(fr.get("map_view", {}).get("full_cells") or []) >= 1
```

- [ ] **Step 2: Patch `build_lab_replay_frames_for_project`**

Replace:

```python
from django_apps.asteroid_lab.services.lab_unified_replay_append import (
    append_algorithm_frames_to_unified_lab_replay,
)
```

With:

```python
from django_apps.asteroid_lab.services.lab_rttp_snapshot_compose import (
    interleave_rttp_snapshot_frames,
    load_rttp_compose_rows_for_project,
)
```

Replace tail:

```python
    milestone_frames, _milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(project_id),
        run_key=None,
    )
    serialized = append_algorithm_frames_to_unified_lab_replay(serialized, milestone_frames)
```

With:

```python
    rttp_rows = load_rttp_compose_rows_for_project(int(project_id))
    serialized = interleave_rttp_snapshot_frames(serialized, rttp_rows)
```

- [ ] **Step 3: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py -v`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(lab-replay): interleave RTTP full-snapshot frames in lab compose"
```

---

## Task 3: Replace H1-R integration and solver entry tests

**Files:**
- Modify: `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_lab_unified_replay_append.py`

- [ ] **Step 1: Replace `test_run_solver_lab_json_unified_replay_includes_rttp_at_tail`**

New name: `test_run_solver_lab_json_h1_s_interleaved_rttp_full_snapshots`

```python
def test_run_solver_lab_json_h1_s_interleaved_rttp_full_snapshots() -> None:
    # ... same setup as current H1-R test ...
    frames = body["lab_replay_frames_json"]
    assert not any(fr.get("render_mode") == "inherited_snapshot" for fr in frames)
    rttp_frames = [fr for fr in frames if fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES]
    assert len(rttp_frames) >= 4
    for fr in rttp_frames:
        assert len(fr.get("map_view", {}).get("full_cells") or []) >= 1
    first_rttp = frames.index(rttp_frames[0])
    assert first_rttp < len(frames) - 1  # not exclusively at very end if map frames follow
    # map-only prefix: types before first RTTP block should exclude RTTP milestones
    prefix = frames[:first_rttp]
    assert {f["event_type"] for f in prefix}.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)
```

- [ ] **Step 2: Update `test_solver_runtime_entry` H1-R block similarly** (no `inherited_snapshot`; full_cells on RTTP frames)

- [ ] **Step 3: Mark `test_lab_unified_replay_append` inherited_snapshot test xfail or delete** — product path removed

- [ ] **Step 4: Run**

Run: `python -m pytest tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/unit/asteroid_lab/test_lab_unified_replay_append.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "test(lab-replay): H1-S interleaved full snapshots; drop H1-R inherited_snapshot"
```

---

## Task 4: Product exposure test + JS render path

**Files:**
- Modify: `tests/unit/web/test_asteroid_lab_page_context.py`
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1: Add failing `test_rttp_track_not_exposed_as_product_timeline`**

```python
@pytest.mark.django_db
def test_rttp_track_not_exposed_as_product_timeline() -> None:
    ctx = alc.lab_page_context_for_project(project_id)  # use existing helper pattern
    assert "lab_replay_frames_json" in ctx
    assert "rttp_replay_frames_json" not in ctx
    assert "optimization_replay" not in ctx
    # diagnostic milestone JSON may exist but is not a second product timeline key:
    if "lab_optimization_milestone_frames_json" in ctx:
        assert ctx["lab_replay_frames_json"] is not ctx.get("lab_optimization_milestone_frames_json")
```

- [ ] **Step 2: Update JS smoke — remove inherited_snapshot requirement**

In `test_lab_js_replay_wiring_smoke`, remove:

```python
    assert "inherited_snapshot" in js
    assert "lastRenderableReplayFrame" in js
    assert "resolveInheritedSnapshotBaseFrame" in js
```

Add:

```python
    assert "overlayCellsFromMapView(mapView)" in js
    assert "function renderReplayFrame" in js
```

- [ ] **Step 3: Remove inherited_snapshot branch from `renderReplayFrame`**

Delete `resolveInheritedSnapshotBaseFrame`, `lastRenderableReplayFrame` usage for product render, and early return that re-renders base frame. Every frame must render from its own `map_view`.

- [ ] **Step 4: Run**

Run: `python -m pytest tests/unit/web/test_asteroid_lab_page_context.py -v`

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(lab-ui): drop inherited_snapshot; single renderReplayFrame path"
```

---

## Task 5: RTTP-G8 + import boundary + PR gate

**Files:**
- Modify: `tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py` (ensure `optimization/` does not import `lab_rttp_snapshot_compose`)

- [ ] **Step 1: Confirm G8 tests still pass**

Run: `python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py::test_rttp_runtime_solver_summary_unchanged_when_replay_persisted -v`

- [ ] **Step 2: Extend import boundary test**

```python
for needle in (
    "lab_optimization_milestone_payload",
    "lab_unified_replay_append",
    "lab_replay_timeline_payload",
    "lab_rttp_snapshot_compose",
):
    assert needle not in opt_source
```

Only `lab_replay_timeline_payload` and `lab_rttp_snapshot_compose` live outside `optimization/` — boundary file should scan `django_apps/asteroid_lab/optimization/` only (existing pattern).

- [ ] **Step 3: Narrow PR gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/unit/web/test_asteroid_lab_page_context.py tests/unit/asteroid_lab/test_optimization_milestone_import_boundary.py -v
python -m ruff check django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
python -m mypy django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py django_apps/asteroid_lab/services/lab_replay_timeline_payload.py
```

- [ ] **Step 4: Commit if fixes only**

```bash
git commit -m "test(lab-replay): 3B-S import boundary and RTTP-G8 gate"
```

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| `:rttp` no product semantics after compose | Task 0 banner; Task 2 loader is compose-only |
| overlay snapshot non-sticky | Task 1 `project_rttp_row` sets overlay per frame |
| PR-1 full_cells from prior renderable | Task 1 `base_map_view` copy |
| 3-tier anchor fallbacks | Task 1 `resolve_insert_index` |
| No new enums PR-1 | Task 1 uses `RTTP_MILESTONE_EVENT_TYPES` |
| No inherited_snapshot | Tasks 1–4 |
| `test_rttp_track_not_exposed_as_product_timeline` | Task 4 |
| RTTP-G8 | Task 5 |
| Same renderReplayFrame | Task 4 |

No placeholders remain.

---

## Execution handoff

Plan saved to `docs/superpowers/plans/2026-05-23-sequence-3b-s-rttp-full-snapshot-replay.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, two-stage review (spec then quality). Use superpowers:subagent-driven-development.

2. **Inline Execution** — this session with superpowers:executing-plans and checkpoints after Task 2 / Task 4.

**Which approach?**

**Branch suggestion:** `feat/sequence-3b-s-rttp-full-snapshot-replay` from `master`.
