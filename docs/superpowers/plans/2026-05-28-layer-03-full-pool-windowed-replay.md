# Layer 03 Full Pool Windowed Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** **APPROVED FOR EXECUTION** (2026-05-28) — Replay Contract Architect amendments applied (candidate_ids coverage, structural L4 base, no per-task commits).

**Goal:** Replace L3 replay “Top 8 of N” with metrics-only `pool_summary` plus up to 10 logical `pool_probe_window` frames that show **every** normal candidate (cell-budget sub-split allowed), without leaking L3 candidate overlays into L4.

**Architecture:** `Layer03Observability` holds the full sorted `replay_pool_candidates` snapshot. `layer03_pool_windowing.py` partitions by logical window and cell budget; each `PoolProbeWindowPlan` carries **`candidate_ids`** for coverage proof. `layer03_segment.py` emits begin → complete → summary (no overlay) → probe_window frames; every probe window projects overlays from **`structural_base_map_view`** (reconstruction or post-L2), not from the previous probe window. **`solver_runtime_assembler.py`** keeps `structural_base_map_view` separate from the last emitted display frame; **L4 MUST use `structural_base_map_view` only.**

**Tech Stack:** Python 3.12+ / Django `asteroid_lab`, replay DTOs, pytest, Lab JS (`asteroid_miner_layout_lab.js`), Tailwind/input.css.

**Spec:** [`docs/superpowers/specs/2026-05-28-layer-03-full-pool-windowed-replay-design.md`](../specs/2026-05-28-layer-03-full-pool-windowed-replay-design.md)

---

## Execution contract (all tasks)

```text
Commit: ONLY when the user explicitly requests git commit.
```

**Checkpoint (replace every former “Step N: Commit”):**

- [ ] **Checkpoint**
  - Do **not** commit unless the user explicitly requests it.
  - Record changed files + pytest/ruff result in the execution report.
  - Suggested commit message (if user approves later): `<one line from task title>`

---

## Blocking amendments (must not skip)

| # | Requirement |
|---|-------------|
| 1 | `PoolProbeWindowPlan.candidate_ids` + probe_window metrics `candidate_ids` / `candidate_count_in_window` |
| 2 | Coverage test: `seen_ids == expected_ids` and no duplicates (not index-range / overlay inference) |
| 3 | Assembler: `structural_base_map_view` for L3 input and **L4 base**; never `l3_frames[-1].map_view` for L4 |
| 4 | `shows_all_candidates` from `candidate_ids` partition; `cell_budget_subsplit_count = max(0, len(plans) - logical_window_count)` |

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/replay/replay_limits.py` | `LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS`; remove `LAYER03_REPLAY_TOP_N` |
| `django_apps/asteroid_lab/replay/event_types.py` | Register `layer03_rim_bundle_pool_probe_window` |
| `django_apps/asteroid_lab/replay/replay_enums.py` | `ReplayEventType.LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW` |
| `django_apps/asteroid_lab/layers/contracts/layer03_observability.py` | `replay_pool_candidates`; `sort_replay_pool_candidates` |
| `django_apps/asteroid_lab/replay/layer03_overlay_cells.py` | **New** — overlay projection + cell count (shared) |
| `django_apps/asteroid_lab/replay/layer03_pool_windowing.py` | **New** — partition + sub-split + `candidate_ids` |
| `django_apps/asteroid_lab/replay/layer03_segment.py` | Summary (no overlay) + probe_window frames |
| `django_apps/asteroid_lab/replay/solver_runtime_assembler.py` | **Modify** — structural vs display base; L4 structural only |
| `tests/unit/asteroid_lab/replay/test_layer03_pool_windowing.py` | **New** — windowing + `candidate_ids` |
| `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py` | Coverage, L4 non-inheritance, ordering |
| `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` | Full pool in observability |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | probe_window tint only; summary metrics HUD |
| `docs/superpowers/specs/2026-05-28-central-solver-runtime-replay-assembler-design.md` | Cross-link + L4 base rule |

---

### Task 1: Event type and replay limits

**Files:**
- Modify: `django_apps/asteroid_lab/replay/replay_limits.py`
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Modify: `django_apps/asteroid_lab/replay/replay_enums.py`
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 1: Write the failing test**

Replace `test_replay_limits_layer03_top_n_constant` with:

```python
def test_replay_limits_layer03_pool_preview_windows_constant() -> None:
    from django_apps.asteroid_lab.replay.replay_limits import (
        LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
        MAX_LAYER04_REPLAY_SELECTED,
    )

    assert LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS == 10
    assert MAX_LAYER04_REPLAY_SELECTED == 32


def test_layer03_probe_window_event_type_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
        SNAPSHOT_EVENT_TYPES,
        is_registered_event_type,
    )
    from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType

    assert EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW in SNAPSHOT_EVENT_TYPES
    assert is_registered_event_type(EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW)
    assert (
        ReplayEventType.LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW.value
        == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    )
```

Update `test_layer03_event_types_registered` to include `EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_probe_window_event_type_registered tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_replay_limits_layer03_pool_preview_windows_constant -v`

Expected: FAIL — missing constant / event type.

- [ ] **Step 3: Implement limits and registration**

`replay_limits.py` — add `LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS = 10`; remove `LAYER03_REPLAY_TOP_N`.

`event_types.py` — add `EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW = "layer03_rim_bundle_pool_probe_window"` to `SNAPSHOT_EVENT_TYPES`.

`replay_enums.py` — add `LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW`.

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_probe_window_event_type_registered tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_replay_limits_layer03_pool_preview_windows_constant tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_event_types_registered -v`

Expected: PASS

- [ ] **Checkpoint** — suggested message if user commits: `feat(replay): register L3 pool_probe_window event and window cap`

---

### Task 2: Layer03Observability — full pool snapshot

**Files:**
- Modify: `django_apps/asteroid_lab/layers/contracts/layer03_observability.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

- [ ] **Step 1: Write the failing test**

In `test_expand_populates_layer03_observability`:

```python
from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
    sort_replay_pool_candidates,
)

def test_expand_populates_layer03_observability() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    assert result.observability.normal_candidate_count == result.metrics.normal_candidate_count
    assert result.observability.skip_reason == result.metrics.layer_skip_reason
    assert len(result.observability.replay_pool_candidates) == len(result.normal_candidates)
    assert result.observability.replay_pool_candidates == sort_replay_pool_candidates(
        result.normal_candidates
    )
```

Remove `assert len(result.observability.top_normal_candidates) <= 8`.

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py::test_expand_populates_layer03_observability -v`

- [ ] **Step 3: Implement**

Rename `select_top_normal_candidates_for_replay` → `sort_replay_pool_candidates` (no `[:top_n]` slice). Replace field `top_normal_candidates` → `replay_pool_candidates`. Update factories and `__all__`.

- [ ] **Step 4: Run test — expect PASS**

- [ ] **Checkpoint** — suggested message: `feat(l3): observability holds full replay_pool_candidates`

---

### Task 3: Pool windowing module (`candidate_ids` + cell budget)

**Files:**
- Create: `django_apps/asteroid_lab/replay/layer03_overlay_cells.py`
- Create: `django_apps/asteroid_lab/replay/layer03_pool_windowing.py`
- Test: `tests/unit/asteroid_lab/replay/test_layer03_pool_windowing.py`

- [ ] **Step 1: Write failing tests**

```python
"""Unit tests for L3 replay pool logical windows and cell-budget sub-split."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    RimBundleCandidate,
    RouteProbedBundleCandidate,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.shared.route_probe import RouteProbeResult
from django_apps.asteroid_lab.replay.layer03_pool_windowing import (
    build_pool_probe_window_plans,
    overlay_cell_count_for_candidate,
)
from django_apps.asteroid_lab.replay.replay_limits import (
    LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
    MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
)


def _entry(cid: str, *, cell_count: int) -> RouteProbedBundleCandidate:
    cells = frozenset((i, 0) for i in range(cell_count))
    candidate = RimBundleCandidate(
        candidate_id=cid,
        equivalence_key=f"eq-{cid}",
        gene_key="g",
        intrinsic_priority_rank=0,
        anchor_coord=(0, 0),
        mining_occupied_cells=cells,
        transport_stub_cells=frozenset(),
        route_probe_start_coord=(0, 0),
        transport_kind=TransportKind.SHAPE_BELT,
        resource_kind="shape",
    )
    path = tuple((i, 1) for i in range(cell_count))
    probe = RouteProbeResult(path_coords=path, path_cost=1)
    return RouteProbedBundleCandidate(candidate=candidate, route_probe_result=probe)


def test_overlay_cell_count_for_candidate_counts_miner_and_path() -> None:
    entry = _entry("a", cell_count=3)
    assert overlay_cell_count_for_candidate(entry) == 6


def test_build_pool_probe_window_plans_partitions_candidate_ids() -> None:
    pool = tuple(_entry(str(i), cell_count=1) for i in range(719))
    plans = build_pool_probe_window_plans(
        replay_pool_candidates=pool,
        max_logical_windows=LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
        max_cells_per_frame=MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
    )
    seen_ids: list[str] = []
    for plan in plans:
        assert plan.candidate_ids == tuple(e.candidate.candidate_id for e in plan.candidates)
        seen_ids.extend(plan.candidate_ids)
    expected_ids = [str(i) for i in range(719)]
    assert seen_ids == expected_ids
    assert len(seen_ids) == len(set(seen_ids))


def test_build_pool_probe_window_plans_empty_pool() -> None:
    assert build_pool_probe_window_plans(replay_pool_candidates=()) == ()


def test_subsplit_when_logical_window_exceeds_cell_budget() -> None:
    heavy = tuple(_entry(str(i), cell_count=120) for i in range(5))
    plans = build_pool_probe_window_plans(
        replay_pool_candidates=heavy,
        max_logical_windows=1,
        max_cells_per_frame=200,
    )
    assert len(plans) > 1
    assert all(p.logical_window_index == 1 for p in plans)
    assert [cid for p in plans for cid in p.candidate_ids] == ["0", "1", "2", "3", "4"]
```

Adjust `RimBundleCandidate` constructor fields per `candidates.py` if collection fails.

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer03_pool_windowing.py -v`

- [ ] **Step 3: Implement `layer03_overlay_cells.py` + `layer03_pool_windowing.py`**

`PoolProbeWindowPlan` MUST include:

```python
@dataclass(frozen=True, slots=True)
class PoolProbeWindowPlan:
    logical_window_index: int
    logical_window_count: int
    physical_subwindow_index: int
    physical_subwindow_count: int
    candidate_start_index: int  # 1-based inclusive
    candidate_end_index: int    # 1-based inclusive
    chunk_size: int
    candidates: tuple[RouteProbedBundleCandidate, ...]
    candidate_ids: tuple[str, ...]  # REQUIRED — coverage SoT
```

When appending each plan:

```python
candidate_ids=tuple(entry.candidate.candidate_id for entry in sub),
```

- [ ] **Step 4: Run tests — expect PASS**

- [ ] **Checkpoint** — suggested message: `feat(replay): L3 pool windowing with candidate_ids partition`

---

### Task 4: Rewrite `layer03_segment` frame emission

**Files:**
- Modify: `django_apps/asteroid_lab/replay/layer03_segment.py` (import overlay from `layer03_overlay_cells.py`)
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 1: Write failing coverage tests**

Replace `test_layer03_pool_summary_overlay_kinds_are_candidate_observation_only` with:

```python
def test_layer03_pool_summary_has_no_overlay_cells() -> None:
    from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import build_solver_runtime_replay_frames
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    candidate_set = rim_bundle_candidate_set_with_observability_for_golden()
    assert candidate_set.observability.replay_pool_candidates

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=candidate_set,
        layer04=None,
    )
    summary = next(
        f for f in frames if f["event_type"] == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY
    )
    assert summary["map_view"]["overlay_cells"] == []
    assert summary["metrics"]["logical_window_count"] >= 1
    assert summary["metrics"]["shows_all_candidates"] is True
    assert summary["metrics"]["pool_preview_overlay_mode"] == "candidate_observation"


def test_layer03_probe_windows_cover_full_replay_pool_by_candidate_ids() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    candidate_set = rim_bundle_candidate_set_with_observability_for_golden()
    expected_ids = [
        entry.candidate.candidate_id
        for entry in candidate_set.observability.replay_pool_candidates
    ]
    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=candidate_set,
        layer04=None,
    )
    window_frames = [
        f
        for f in frames
        if f["event_type"] == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    ]
    assert window_frames

    seen_ids = [cid for fr in window_frames for cid in fr["metrics"]["candidate_ids"]]

    assert seen_ids == expected_ids
    assert len(seen_ids) == len(set(seen_ids))

    for fr in window_frames:
        m = fr["metrics"]
        assert m["candidate_count_in_window"] == len(m["candidate_ids"])
        assert m["candidate_start_index"] <= m["candidate_end_index"]
```

- [ ] **Step 2: Run tests — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_pool_summary_has_no_overlay_cells tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_probe_windows_cover_full_replay_pool_by_candidate_ids -v`

- [ ] **Step 3: Implement segment emission**

Helper for summary metrics (in `layer03_segment.py`):

```python
def _pool_summary_metrics(
    observability: Layer03Observability,
    plans: tuple[PoolProbeWindowPlan, ...],
) -> dict[str, object]:
    shown_ids = tuple(cid for plan in plans for cid in plan.candidate_ids)
    expected_ids = tuple(
        entry.candidate.candidate_id for entry in observability.replay_pool_candidates
    )
    logical_window_count = plans[0].logical_window_count if plans else 0
    return {
        "layer": LAYER03_PHASE,
        "normal_candidate_count": observability.normal_candidate_count,
        "route_probe_succeeded_count": observability.route_probe_succeeded_count,
        "logical_window_count": logical_window_count,
        "physical_probe_window_frame_count": len(plans),
        "shows_all_candidates": shown_ids == expected_ids,
        "pool_preview_overlay_mode": "candidate_observation",
        "cell_budget_subsplit_count": max(0, len(plans) - logical_window_count),
    }
```

**Summary frame:** `overlay_cells=()`, description e.g. `Replay pool 719 candidate(s) · 10 logical window(s) · 12 preview frame(s)`.

**Each probe_window frame** metrics MUST include:

```python
{
    "layer": LAYER03_PHASE,
    "probe_succeeded_count": observability.route_probe_succeeded_count,
    "normal_candidate_count": observability.normal_candidate_count,
    "logical_window_index": plan.logical_window_index,
    "logical_window_count": plan.logical_window_count,
    "physical_subwindow_index": plan.physical_subwindow_index,
    "physical_subwindow_count": plan.physical_subwindow_count,
    "candidate_start_index": plan.candidate_start_index,
    "candidate_end_index": plan.candidate_end_index,
    "chunk_size": plan.chunk_size,
    "candidate_ids": list(plan.candidate_ids),
    "candidate_count_in_window": len(plan.candidates),
    "shows_all_candidates": True,  # per-frame hint; summary carries authoritative flag
}
```

Each probe window calls `_timeline_frame(..., base_map_view=structural_base_passed_in, overlay_cells=...)` — segment receives **structural** base from assembler; each window overlays only `plan.candidates` (no accumulation across windows).

Return `(begin, complete, summary, *probe_windows)`.

- [ ] **Step 4: Run replay unit tests**

Run: `python -m pytest tests/unit/asteroid_lab/replay/ tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py -v`

- [ ] **Step 5: Ruff**

Run: `python -m ruff check django_apps/asteroid_lab/replay/ django_apps/asteroid_lab/layers/contracts/layer03_observability.py`

- [ ] **Checkpoint** — suggested message: `feat(replay): L3 pool summary TOC and probe_window frames with candidate_ids`

---

### Task 5: Assembler — structural base vs L4 (blocking)

**Files:**
- Modify: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`
- Fixture (if missing): `layer04_result_with_selection_for_golden()` in `replay_assembler_fixtures.py`

- [ ] **Step 1: Write failing tests**

```python
def test_assembler_l3_probe_windows_follow_summary() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
    )
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_with_observability_for_golden,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=rim_bundle_candidate_set_with_observability_for_golden(),
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert types.index(EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY) < types.index(
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    )


def test_l4_segment_does_not_inherit_l3_candidate_overlay() -> None:
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

    l4_frames = [f for f in frames if str(f["event_type"]).startswith("layer04_")]

    for fr in l4_frames:
        map_view = fr["map_view"]
        inherited = [
            row
            for row in (map_view.get("full_cells") or []) + (map_view.get("overlay_cells") or [])
            if str(row.get("kind", "")).startswith("candidate_")
        ]
        assert inherited == []
```

Implement `layer04_result_with_selection_for_golden()` using existing `run_layer_04_rim_bundle_placement` + golden fixtures (same pattern as `test_assembler_emits_l2_then_l4_when_layer04_present`).

- [ ] **Step 2: Run tests — expect FAIL** on `test_l4_segment_does_not_inherit_l3_candidate_overlay` until assembler fixed.

- [ ] **Step 3: Implement assembler split**

In `build_solver_runtime_replay_frames`:

```python
    structural_base_map_view = (
        replay_map_view_from_json_dict(source["map_view"])
        if source is not None
        else map_view_from_complete_map(complete_map)
    )

    if exterior_plan_wire is not None:
        l2_frame = build_layer02_exterior_transport_frame(...)
        frames.append(l2_frame)
        structural_base_map_view = l2_frame.map_view

    if layer03 is not None:
        l3_base = _ensure_renderable_base_map_view(
            structural_base_map_view,
            complete_map=complete_map,
        )
        l3_frames = build_layer03_runtime_segment_frames(
            observability=layer03.observability,
            base_map_view=l3_base,
        )
        frames.extend(l3_frames)
        # DO NOT assign structural_base_map_view = l3_frames[-1].map_view

    if layer04 is not None:
        l4_base = _ensure_renderable_base_map_view(
            structural_base_map_view,  # NOT last L3 probe_window
            complete_map=complete_map,
        )
        l4_frames = build_layer04_runtime_segment_frames(
            base_map_view=l4_base,
            selected=layer04.selected_placements,
            rejected=layer04.rejected_candidates,
        )
        frames.extend(l4_frames)
```

Remove any `current_base_map_view = l3_frames[-1].map_view` pattern.

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py -v`

- [ ] **Checkpoint** — suggested message: `fix(replay): L4 uses structural base without L3 candidate overlay`

---

### Task 6: UI verification

**Files:**
- Verify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js`

- [ ] **Step 1:** `isL3PoolCandidateObservationFrame` — **only** `layer03_rim_bundle_pool_probe_window` (not `pool_summary`).

- [ ] **Step 2:** Summary frame HUD from backend metrics when `description` empty.

- [ ] **Step 3:** Manual — summary: no tint; probe_window: tint + asteroid ring on field.

- [ ] **Checkpoint** — suggested message: `fix(lab-ui): L3 pool summary metrics-only HUD`

---

### Task 7: Documentation cross-links

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-central-solver-runtime-replay-assembler-design.md`

- [ ] **Step 1:** Link full-pool windowed spec; document `replay_pool_candidates`, probe_window, **structural L4 base**, `candidate_ids` coverage.

- [ ] **Checkpoint** — suggested message: `docs(replay): central assembler spec links full-pool windowed L3`

---

### Task 8: Full gate (iteration)

- [ ] **Step 1:** `python -m pytest tests/unit/asteroid_lab/replay/ tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py -v`

- [ ] **Step 2:** `python -m ruff check django_apps/asteroid_lab/replay/ django_apps/asteroid_lab/layers/contracts/layer03_observability.py`

- [ ] **Step 3:** `python -m mypy django_apps/asteroid_lab/replay/layer03_pool_windowing.py django_apps/asteroid_lab/replay/layer03_segment.py django_apps/asteroid_lab/replay/solver_runtime_assembler.py django_apps/asteroid_lab/layers/contracts/layer03_observability.py`

- [ ] **Checkpoint** — report all green before claiming complete.

---

## Spec self-review (post-amendment)

| Spec requirement | Task |
|------------------|------|
| `replay_pool_candidates` | Task 2 |
| Remove `TOP_N` | Task 1 |
| `pool_summary` metrics-only | Task 4 |
| `candidate_ids` coverage SoT | Task 3, 4 |
| probe_window overlays only | Task 4 |
| ≤10 logical windows | Task 3 |
| Cell-budget sub-split | Task 3 |
| L4 structural base (no L3 overlay) | Task 5 |
| UI tint / sprite ring | Task 6 |
| Event registration | Task 1 |

**Placeholder scan:** None.

---

## Execution handoff

**Plan revised and approved for execution:** `docs/superpowers/plans/2026-05-28-layer-03-full-pool-windowed-replay.md`

**Recommended:** **Subagent-Driven** — Task별 구현 → Replay Contract review → 다음 Task.

When ready to implement, say **「Subagent-Driven으로 Task 1부터」** or **「Inline으로 진행」**. Commits only when you explicitly request them.
