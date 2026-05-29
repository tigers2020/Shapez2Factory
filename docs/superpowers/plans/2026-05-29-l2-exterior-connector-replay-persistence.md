# L2 Exterior Connector Replay Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `planned_exterior_connector` visible on all L3/L4 solver-runtime replay frames and fix Lab lazy replay track metrics so exterior transport spots never disappear during rim bundle scan.

**Architecture:** Persistent connector overlays are rebuilt from `exterior_connector_plan` wire (SoT). L3/L4 segments emit **transient-only** `ReplaySegmentFrameSpec`; `solver_runtime_assembler` composes structural + persistent + transient wire overlays and attaches `metrics.exterior_connector_plan`. Lab JS refreshes `replayTrackMetrics` on lazy load.

**Tech Stack:** Python 3.12+ / Django `asteroid_lab`, replay DTOs, pytest, ruff, Lab JS (`asteroid_miner_layout_lab.js`).

**Spec:** [`docs/superpowers/specs/2026-05-29-l2-exterior-connector-replay-persistence-design.md`](../specs/2026-05-29-l2-exterior-connector-replay-persistence-design.md)

---

## Execution contract (all tasks)

```text
Commit: ONLY when the user explicitly requests git commit.
```

**Checkpoint (replace every former “Step N: Commit”):**

- [ ] **Checkpoint**
  - Do **not** commit unless the user explicitly requests it.
  - Record changed files + pytest/ruff result in the execution report.
  - Suggested commit message (if user approves later): `fix(replay): persist L2 exterior connectors through L3/L4 runtime frames`

---

## Blocking amendments (must not skip)

| # | Requirement |
|---|-------------|
| 1 | Persistent overlay SoT = `exterior_connector_plan` wire via `_planned_connectors`; not L2 frame overlay |
| 2 | L3/L4 segments emit `ReplaySegmentFrameSpec` (transient only); assembler owns final `map_view` |
| 3 | `test_layer03_pool_summary_has_no_overlay_cells` → assert no **candidate** overlay + assert **has** connector overlay |
| 4 | Attach `metrics.exterior_connector_plan` for every frame after wire becomes available |

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/replay/overlay_composition.py` | **New** — `compose_replay_overlay_cells`, dedupe keys |
| `django_apps/asteroid_lab/replay/segment_frame_spec.py` | **New** — `ReplaySegmentFrameSpec` frozen dataclass |
| `django_apps/asteroid_lab/replay/persistent_exterior_overlay.py` | **New** — `persistent_connector_overlays_from_wire(plan_wire)` wrapping enrichment helper |
| `django_apps/asteroid_lab/replay/layer03_segment.py` | Emit specs only; remove `_timeline_frame` map composition |
| `django_apps/asteroid_lab/replay/layer04_segment.py` | Emit specs only |
| `django_apps/asteroid_lab/replay/solver_runtime_assembler.py` | Compose overlays + metrics; finalize wire JSON |
| `django_apps/asteroid_lab/replay/timeline_serialization.py` | Optional: `overlay_cells_wire` patch helper for dict rows with `overlay_role` |
| `tests/unit/asteroid_lab/replay/test_overlay_composition.py` | **New** |
| `tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py` | **New** |
| `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py` | Update pool_summary test |
| `tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py` | **New** — JS contract |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Lazy `replay_track_metrics` refresh |

---

### Task 1: Overlay composition helper (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/replay/overlay_composition.py`
- Create: `tests/unit/asteroid_lab/replay/test_overlay_composition.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/asteroid_lab/replay/test_overlay_composition.py`:

```python
"""Tests for replay overlay layer composition."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.overlay_composition import compose_replay_overlay_cells


def _conn(x: int, y: int, connector_id: str = "ext_00") -> dict[str, object]:
    return {
        "x": x,
        "y": y,
        "overlay_role": "planned_exterior_connector",
        "connector_id": connector_id,
        "connector_role": "required",
        "tile_type": "SpaceBelt_Forward",
        "rotation": 0,
    }


def _cand(x: int, y: int, kind: str = "candidate_miner") -> dict[str, object]:
    return {"x": x, "y": y, "kind": kind, "transport": "shape_belt"}


def test_compose_preserves_connector_and_candidate_at_same_coord() -> None:
    out = compose_replay_overlay_cells(
        structural_overlay_cells=[],
        persistent_overlay_cells=[_conn(5, -6)],
        transient_overlay_cells=[_cand(5, -6)],
    )
    roles = {str(c.get("overlay_role") or c.get("kind")) for c in out}
    assert "planned_exterior_connector" in roles
    assert "candidate_miner" in roles


def test_compose_dedupes_exact_connector_duplicate_only() -> None:
    dup = _conn(5, -6, connector_id="ext_00")
    out = compose_replay_overlay_cells(
        structural_overlay_cells=[],
        persistent_overlay_cells=[dup, dict(dup)],
        transient_overlay_cells=[],
    )
    connectors = [c for c in out if c.get("overlay_role") == "planned_exterior_connector"]
    assert len(connectors) == 1


def test_compose_orders_structural_then_persistent_then_transient() -> None:
    structural = [{"x": 0, "y": 0, "overlay_role": "decode", "kind": "internal_void"}]
    persistent = [_conn(1, 0)]
    transient = [_cand(2, 0)]
    out = compose_replay_overlay_cells(
        structural_overlay_cells=structural,
        persistent_overlay_cells=persistent,
        transient_overlay_cells=transient,
    )
    assert out[0]["overlay_role"] == "decode"
    assert out[1]["overlay_role"] == "planned_exterior_connector"
    assert out[2]["kind"] == "candidate_miner"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_composition.py -v`

Expected: FAIL — `ModuleNotFoundError: overlay_composition`

- [ ] **Step 3: Implement `overlay_composition.py`**

Create `django_apps/asteroid_lab/replay/overlay_composition.py`:

```python
"""Compose replay map_view overlay_cells layers (output-only)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

_CONNECTOR_ROLE = "planned_exterior_connector"


def _connector_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("overlay_role") or ""),
        int(row["x"]),
        int(row["y"]),
        str(row.get("connector_id") or ""),
    )


def _candidate_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    key: list[object] = [
        str(row.get("overlay_role") or ""),
        str(row.get("kind") or ""),
        int(row["x"]),
        int(row["y"]),
    ]
    if row.get("candidate_id") is not None:
        key.append(str(row["candidate_id"]))
    if row.get("transport") is not None:
        key.append(str(row["transport"]))
    return tuple(key)


def _structural_dedupe_key(row: Mapping[str, object]) -> tuple[object, ...]:
    return (
        str(row.get("overlay_role") or ""),
        str(row.get("kind") or ""),
        int(row["x"]),
        int(row["y"]),
    )


def _dedupe_rows(rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    out: list[dict[str, object]] = []
    for row in rows:
        data = dict(row)
        role = str(data.get("overlay_role") or "")
        if role == _CONNECTOR_ROLE:
            key = _connector_dedupe_key(data)
        elif role:
            key = _structural_dedupe_key(data)
        else:
            key = _candidate_dedupe_key(data)
        if key in seen:
            continue
        seen.add(key)
        out.append(data)
    return out


def _non_connector_structural_rows(
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        dict(r)
        for r in rows
        if str(r.get("overlay_role") or "") != _CONNECTOR_ROLE
    ]


def compose_replay_overlay_cells(
    *,
    structural_overlay_cells: Sequence[Mapping[str, object]],
    persistent_overlay_cells: Sequence[Mapping[str, object]],
    transient_overlay_cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Merge overlay layers; persistent connector rows must come from plan wire."""

    structural = _non_connector_structural_rows(structural_overlay_cells)
    persistent = [dict(r) for r in persistent_overlay_cells]
    transient = [dict(r) for r in transient_overlay_cells]
    return _dedupe_rows([*structural, *persistent, *transient])


__all__ = ["compose_replay_overlay_cells"]
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_overlay_composition.py -v`

Expected: PASS

- [ ] **Checkpoint** (see execution contract)

---

### Task 2: Persistent overlay from plan wire

**Files:**
- Create: `django_apps/asteroid_lab/replay/persistent_exterior_overlay.py`
- Modify: `tests/unit/asteroid_lab/replay/test_overlay_composition.py` (import wire helper test)

- [ ] **Step 1: Write failing test**

Append to `test_overlay_composition.py` or new file `test_persistent_exterior_overlay.py`:

```python
from django_apps.asteroid_lab.replay.persistent_exterior_overlay import (
    persistent_connector_overlays_from_wire,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    exterior_plan_wire_for_golden,
)


def test_persistent_overlay_from_wire_has_planned_role() -> None:
    wire = exterior_plan_wire_for_golden()
    rows = persistent_connector_overlays_from_wire(wire)
    assert rows
    assert all(r.get("overlay_role") == "planned_exterior_connector" for r in rows)
    assert all("x" in r and "y" in r for r in rows)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_persistent_exterior_overlay.py -v`  
(or the module where the test was added)

- [ ] **Step 3: Implement**

Create `django_apps/asteroid_lab/replay/persistent_exterior_overlay.py`:

```python
"""Rebuild persistent L2 exterior connector overlay rows from plan wire (SoT)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    _planned_connectors,
)


def persistent_connector_overlays_from_wire(
    plan_wire: Mapping[str, object],
) -> list[dict[str, Any]]:
    return list(_planned_connectors(dict(plan_wire)))


__all__ = ["persistent_connector_overlays_from_wire"]
```

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Checkpoint**

---

### Task 3: `ReplaySegmentFrameSpec` + L3 segment refactor

**Files:**
- Create: `django_apps/asteroid_lab/replay/segment_frame_spec.py`
- Modify: `django_apps/asteroid_lab/replay/layer03_segment.py`
- Create: `tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py`

- [ ] **Step 1: Write failing assembler integration tests**

Create `tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py`:

```python
"""L3 runtime frames must retain L2 exterior connector observability."""

from __future__ import annotations

_CANDIDATE_KINDS = frozenset(
    {
        "candidate_miner",
        "candidate_transport_stub",
        "candidate_route_path",
    }
)


def _overlay_roles(frame: dict) -> set[str]:
    mv = frame.get("map_view") or {}
    overlay = mv.get("overlay_cells") or []
    roles: set[str] = set()
    for row in overlay:
        if not isinstance(row, dict):
            continue
        if row.get("overlay_role"):
            roles.add(str(row["overlay_role"]))
        if row.get("kind") in _CANDIDATE_KINDS:
            roles.add("candidate_overlay")
    return roles


def _has_connector_overlay(frame: dict) -> bool:
    mv = frame.get("map_view") or {}
    for row in mv.get("overlay_cells") or []:
        if isinstance(row, dict) and row.get("overlay_role") == "planned_exterior_connector":
            return True
    return False


def _frames_with_plan() -> list[dict]:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    return build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
    )


def test_l3_scan_begin_preserves_planned_exterior_connector_overlay() -> None:
    frames = _frames_with_plan()
    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    assert _has_connector_overlay(begin)


def test_l3_probe_window_preserves_connector_and_candidate_overlay() -> None:
    frames = _frames_with_plan()
    probe = next(
        f for f in frames if f["event_type"] == "layer03_rim_bundle_pool_probe_window"
    )
    assert _has_connector_overlay(probe)
    mv = probe["map_view"]
    kinds = {str(c.get("kind")) for c in mv.get("overlay_cells") or [] if isinstance(c, dict)}
    assert kinds & _CANDIDATE_KINDS


def test_l3_runtime_frame_has_exterior_connector_plan_metrics() -> None:
    from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
        METRICS_KEY,
    )

    frames = _frames_with_plan()
    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    wire = (begin.get("metrics") or {}).get(METRICS_KEY)
    assert isinstance(wire, dict)
    assert isinstance(wire.get("planned_connectors"), list)


def test_l3_pool_summary_has_no_candidate_overlay_but_has_connector() -> None:
    frames = _frames_with_plan()
    summary = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_pool_summary")
    overlay = summary["map_view"]["overlay_cells"]
    assert not any(
        isinstance(c, dict) and str(c.get("kind") or "") in _CANDIDATE_KINDS for c in overlay
    )
    assert _has_connector_overlay(summary)
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py -v`

- [ ] **Step 3: Add `ReplaySegmentFrameSpec`**

Create `django_apps/asteroid_lab/replay/segment_frame_spec.py`:

```python
"""Transient-only replay segment frame specs (assembler composes final map_view)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell


@dataclass(frozen=True, slots=True)
class ReplaySegmentFrameSpec:
    event_type: ReplayEventType
    phase: ReplayPhase
    title: str
    description: str
    metrics: dict[str, object]
    transient_overlay_cells: tuple[ReplayOverlayCell, ...] = ()
    inspector: dict[str, Any] = field(default_factory=dict)


__all__ = ["ReplaySegmentFrameSpec"]
```

- [ ] **Step 4: Refactor `layer03_segment.py`**

- Rename `build_layer03_runtime_segment_frames` → `build_layer03_runtime_segment_specs` returning `tuple[ReplaySegmentFrameSpec, ...]`.
- Remove `_timeline_frame` and `base_map_view` parameter.
- Each spec carries only `transient_overlay_cells` (empty for begin/complete/summary; populated for probe_window).
- Keep existing metrics builders unchanged.

Export alias for transition if needed:

```python
# Deprecated name — remove after assembler wired
build_layer03_runtime_segment_frames = build_layer03_runtime_segment_specs
```

Prefer updating assembler only and deleting old name in same task.

- [ ] **Step 5: Wire assembler (partial — L3 only)**

In `solver_runtime_assembler.py`:

1. After L2 frame, set `exterior_plan_wire_dict` and `persistent_overlays = persistent_connector_overlays_from_wire(wire)` when wire is not None.
2. Extract `structural_overlay_wire` from reconstruction source frame map_view (non-connector rows only) — may be empty list.
3. Add helper `_transient_overlay_wire(cells: tuple[ReplayOverlayCell, ...]) -> list[dict]` mapping to `{"x","y","kind","transport",...}`.
4. Add `_compose_frame_from_spec(spec, *, structural_map_view, persistent_overlays, plan_wire)` building `ReplayTimelineFrame` with composed overlay wire patched into JSON via:

```python
def _finalize_frame_wire(
    frame: ReplayTimelineFrame,
    *,
    overlay_cells_wire: list[dict[str, object]],
    metrics: dict[str, object],
) -> dict[str, object]:
    from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
        METRICS_KEY,
    )
    wire = replay_timeline_frame_to_json_dict(frame)
    merged_metrics = dict(metrics)
    if plan_wire is not None:
        merged_metrics[METRICS_KEY] = dict(plan_wire)
    wire["metrics"] = merged_metrics
    mv = dict(wire["map_view"])
    mv["overlay_cells"] = overlay_cells_wire
    wire["map_view"] = mv
    return wire
```

5. Replace `build_layer03_runtime_segment_frames(...)` call with spec builder + per-spec finalize.

**Important:** `structural_base_map_view` for L4 remains separate (post-L2 full_cells, not display overlay).

- [ ] **Step 6: Run L3 persistence tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py -v`

- [ ] **Step 7: Fix `test_layer03_pool_summary_has_no_overlay_cells` in `test_solver_runtime_assembler.py`**

Rename to `test_layer03_pool_summary_has_no_candidate_overlay_but_has_connector` and replace body with asserts from new test file (or delete duplicate and keep one).

Remove: `assert summary["map_view"]["overlay_cells"] == []`

- [ ] **Step 8: Run assembler tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py -v`

- [ ] **Checkpoint**

---

### Task 4: L4 segment + assembler

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer04_segment.py`
- Modify: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`
- Modify: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 1: Write failing test**

Add to `test_layer03_exterior_connector_overlay_persistence.py` (or assembler test file):

```python
def test_l4_placement_begin_preserves_planned_exterior_connector_overlay() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        layer04_result_with_selection_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=layer04_result_with_selection_for_golden(),
    )
    begin = next(f for f in frames if f["event_type"] == "layer04_rim_placement_begin")
    assert _has_connector_overlay(begin)
    assert (begin.get("metrics") or {}).get("exterior_connector_plan")
```

(Use existing golden fixture name from `replay_assembler_fixtures.py` — verify import; adjust to `layer04` fixture actually exported.)

- [ ] **Step 2: Run test — expect FAIL**

- [ ] **Step 3: Refactor `layer04_segment.py` to specs**

Same pattern as L3: `build_layer04_runtime_segment_specs(...) -> tuple[ReplaySegmentFrameSpec, ...]`.

- [ ] **Step 4: Assembler composes L4 frames with same `_compose_frame_from_spec`**

Use `structural_base_map_view` (not last L3 display frame) for `full_cells` / `bbox` / `base_ref`.

- [ ] **Step 5: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_exterior_connector_overlay_persistence.py tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py -v`

- [ ] **Checkpoint**

---

### Task 5: Lab lazy UI — `replay_track_metrics`

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`
- Create: `tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py`

- [ ] **Step 1: Write failing JS contract test**

Create `tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py`:

```python
"""Lab lazy replay must refresh track metrics (frozen exterior plan)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_apply_loaded_lab_replay_payload_assigns_replay_track_metrics() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "function applyLoadedLabReplayPayload(payload)" in js
    assert "payload.replay_track_metrics" in js
    assert "replayTrackMetrics = payload.replay_track_metrics" in js


def test_lazy_replace_lab_replay_payload_applies_track_metrics_before_early_return() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    # lazy branch must not return before reading replay_track_metrics from POST payload
    idx_lazy = js.find('lazy.mode === "lazy"')
    assert idx_lazy >= 0
    chunk = js[idx_lazy : idx_lazy + 1200]
    assert "replay_track_metrics" in chunk or "replayTrackMetrics" in chunk
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py -v`

- [ ] **Step 3: Patch `asteroid_miner_layout_lab.js`**

In `applyLoadedLabReplayPayload`:

```javascript
function applyLoadedLabReplayPayload(payload) {
  if (!payload || !Array.isArray(payload.frames)) return;
  if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
    replayTrackMetrics = payload.replay_track_metrics;
  }
  const prevIndex = replayArrayIndex;
  // ... rest unchanged
}
```

In `replaceLabReplayPayload`, inside `if (lazy && lazy.mode === "lazy") {` block, **before** `return`:

```javascript
if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
  replayTrackMetrics = payload.replay_track_metrics;
}
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py -v`

- [ ] **Checkpoint**

---

### Task 6: Ruff + regression sweep

**Files:** (none new)

- [ ] **Step 1: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/replay django_apps/asteroid_lab/services/lab_timeline_exterior_connector_enrichment.py`

Expected: PASS

- [ ] **Step 2: Replay unit sweep**

Run: `python -m pytest tests/unit/asteroid_lab/replay/ tests/unit/asteroid_lab/test_lab_timeline_exterior_connector_enrichment.py tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py -v`

Expected: PASS

- [ ] **Step 3: Optional integration**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py -v`

Expected: PASS

- [ ] **Checkpoint**

---

## Plan self-review (spec coverage)

| Spec § | Task |
|--------|------|
| §2 Persistent SoT from wire | Task 2, 3 |
| §2 Composition order / dedupe | Task 1 |
| §3 Segment transient-only | Task 3, 4 |
| §3 Assembler authority | Task 3, 4 |
| §4 Pool summary semantics | Task 3 (test rename) |
| §5 Lab lazy UI | Task 5 |
| §6 Wire dict overlay_role | Task 3 `_finalize_frame_wire` |
| §7 Tests | Tasks 1–5 |

No placeholders remain. L4 golden fixture name: verify in `replay_assembler_fixtures.py` during Task 4 Step 1.

---

## Execution handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-29-l2-exterior-connector-replay-persistence.md`.**

**Spec saved to `docs/superpowers/specs/2026-05-29-l2-exterior-connector-replay-persistence-design.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — implement in this session with checkpoints

Which approach do you want?
