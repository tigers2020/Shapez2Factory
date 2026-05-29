# Central Solver Runtime Replay Assembler — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reunify split replay authority under `django_apps/asteroid_lab/replay/`, emit L2→L3→L4 `solver_runtime_replay_frames` from one assembler, and expose L3 progress on the Lab timeline via `Layer03Observability` (not layer-local replay modules).

**Architecture:** Move L2/L4 frame projection from `services/lab_layer02_timeline.py` and `layers/layer_04/.../replay.py` into `replay/layer02_segment.py`, `replay/layer03_segment.py`, `replay/layer04_segment.py`. `replay/solver_runtime_assembler.py` owns ordering and JSON output. Layers return algorithm DTOs + observability only; `run_layer04` stops building `ReplayFrameAppendDTO` lists (pass `replay_frames=()` until field removal in v1.1).

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`), frozen dataclasses, `ReplayTimelineFrame` wire

**Spec:** [`2026-05-28-central-solver-runtime-replay-assembler-design.md`](../specs/2026-05-28-central-solver-runtime-replay-assembler-design.md) — **APPROVED (2026-05-28)** Replay Contract Architect

**Plan status:** **APPROVED (2026-05-28)** — Replay Contract Architect (amendments: no ellipsis in tests, assembler-owned `current_base_map_view`, L3 skip on `scan_complete`, Task 0 inventory evidence)

**Work classification:** contract change · implementation change

**Branch suggestion:** `feat/central-solver-runtime-replay-assembler`

**pytest:** No `-q`, `--quiet`, or `--tb=no`.

**Commit:** only when the user explicitly requests git commit.

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/replay/solver_runtime_assembler.py` |
| Create | `django_apps/asteroid_lab/replay/layer02_segment.py` |
| Create | `django_apps/asteroid_lab/replay/layer03_segment.py` |
| Create | `django_apps/asteroid_lab/replay/layer04_segment.py` |
| Create | `django_apps/asteroid_lab/layers/contracts/layer03_observability.py` |
| Modify | `django_apps/asteroid_lab/replay/event_types.py` |
| Modify | `django_apps/asteroid_lab/replay/replay_enums.py` |
| Modify | `django_apps/asteroid_lab/replay/replay_limits.py` |
| Modify | `django_apps/asteroid_lab/replay/__init__.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/candidates.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py` |
| Modify | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py` |
| Delete | `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/replay.py` |
| Modify | `django_apps/asteroid_lab/services/lab_layer02_timeline.py` |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_layer02.py` |
| Modify | `django_apps/asteroid_lab/layers/contracts/rim_placement.py` (docstring deprecate `replay_frames`) |
| Create | `tests/unit/asteroid_lab/replay/fixtures/replay_assembler_fixtures.py` |
| Create | `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py` |
| Create | `docs/superpowers/reports/2026-05-28-replay-authority-inventory.md` (Task 0 evidence; filled at PR open) |
| Create | `tests/unit/asteroid_lab/replay/test_layer04_segment.py` |
| Create | `tests/unit/asteroid_lab/replay/test_replay_authority_gates.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py` |
| Modify | `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py` (factory observability) |
| Create | `tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py` |
| Patch | `docs/superpowers/specs/2026-05-28-layer-04-rim-bundle-placement-design.md` |
| Patch | `docs/superpowers/specs/2026-05-28-layer-03-rim-mining-bundles-design.md` |

---

## Execution order

```text
Task 0  — Authority inventory (grep table; no code)
Task 1  — L3 event types + replay limits constants
Task 2  — layer02_segment + assembler skeleton (L2-only parity test)
Task 3  — layer04_segment migrate; delete layer replay.py; update L4 tests
Task 4  — Layer03Observability contract + expand population
Task 5  — layer03_segment + assembler L3 wire
Task 6  — Full assembler + solver_runtime_layer02 wire + L2-missing-plan test
Task 7  — Authority gate tests + timeline integration test
Task 8  — Deprecation wrappers + doc patches
Task 9  — PR gate (pytest narrow → ruff → mypy)
```

**Optional PR split:** PR-A Tasks 1–3 + 8 (reunify L2/L4, no L3 frames yet). PR-B Tasks 4–7 (L3 observability + timeline).

---

## Assembler-owned `current_base_map_view` (normative)

Segment builders **MUST NOT** scan prior frames or discover timeline state. Only `solver_runtime_assembler.py` updates the running base.

```text
current_base_map_view := map_view_from_reconstruction_complete_source(lab_frames, complete_map)

If exterior_plan_wire is not None:
  emit L2 frame
  current_base_map_view := L2_frame.map_view

If layer03 is not None:
  emit L3 begin / complete / pool summary (per skip rules)
  current_base_map_view := L3_pool_summary_frame.map_view   # last L3 frame emitted

If layer04 is not None:
  build_layer04_runtime_segment_frames(..., base_map_view=current_base_map_view)
  append L4 frames (assembler does not re-read L3/L2 lists)
```

`build_layer04_runtime_segment_frames` and `build_layer03_runtime_segment_frames` take `base_map_view: ReplayMapView` as an explicit parameter — no optional discovery inside segment modules.

---

## Shared test fixtures (create in Task 2 Step 0)

**File:** `tests/unit/asteroid_lab/replay/fixtures/replay_assembler_fixtures.py`

All assembler tests import from here. **No ellipsis in test bodies.**

```python
"""Fixtures for central solver runtime replay assembler tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    build_rim_bundle_candidate_set,
)
from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
    build_layer03_observability_for_test,
)
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)


def reconstruction_complete_lab_frame_dict_for_golden() -> dict[str, object]:
    """Minimal renderable reconstruction.completed wire (matches test_lab_layer02_timeline pattern)."""
    complete = golden_5x5_complete_map()
    rows = [
        {"x": x, "y": y, "kind": "asteroid_shape_field", "transport": "", "rotation": 0}
        for x, y in sorted(complete.field_cells)
    ]
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    return {
        "frame_index": 0,
        "event_type": ReplayEventType.RECONSTRUCTION_COMPLETED.value,
        "phase": "reconstruction",
        "map_view": {
            "full_cells": rows,
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {
                "min_x": min(xs),
                "min_y": min(ys),
                "max_x": max(xs),
                "max_y": max(ys),
            },
        },
        "metrics": {},
    }


def exterior_plan_wire_for_golden() -> dict[str, object]:
    metrics = exterior_connector_plan_to_metrics_dict(minimal_l2_plan_for_golden())
    wire = metrics["exterior_connector_plan"]
    assert isinstance(wire, dict)
    return wire


def renderable_base_map_view_for_golden() -> ReplayMapView:
    return replay_map_view_from_json_dict(
        reconstruction_complete_lab_frame_dict_for_golden()["map_view"]
    )


def rim_bundle_candidate_set_missing_exterior_plan() -> object:
    """Post-Task-4: hold set with MISSING_EXTERIOR_CONNECTION_PLAN observability."""
    obs = build_layer03_observability_for_test(
        skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN,
        rim_anchor_count=0,
        top_normal_candidates=(),
    )
    return build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=0,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=0,
            route_probe_succeeded_count=0,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=0,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN,
        ),
        observability=obs,
    )


def rim_bundle_candidate_set_with_observability_for_golden() -> object:
    """Post-Task-4: run expand_rim_bundle_candidates with golden map + L2 plan + two_seed_catalog()."""
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
        expand_rim_bundle_candidates,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
        minimal_l2_plan_for_golden,
        two_seed_catalog,
    )

    return expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
```

**Task 2 Step 0:** create this file before any assembler test that references golden inputs. Omit `rim_bundle_*` helpers until Task 4 observability exists, or gate those tests with `pytest.importorskip`.

---

## Task 0: Replay authority inventory

**Deliverables (all required — no production code):**

1. Run grep/classify (table below).
2. **Copy the filled table into the PR description** under `## Replay authority inventory`.
3. **Append the same table** to `docs/superpowers/reports/2026-05-28-replay-authority-inventory.md` with date and branch name (commit this report file with the PR).
4. Update **Inventory results** section at the bottom of this plan (checkbox when done).

Run and classify each hit:

```powershell
rg -n "solver_runtime_replay_frames|replay_frames|ReplayFrameAppendDTO|build_.*runtime_replay_frames|layers/.*/replay\.py" django_apps tests --glob "!**/__pycache__/**"
```

| Expected hit | Classification |
|--------------|----------------|
| `replay/event_types.py` | `canonical_owner` |
| `replay/solver_runtime_assembler.py` (new) | `canonical_owner` |
| `replay/layer02_segment.py` (new) | `segment_projection` |
| `replay/layer03_segment.py` (new) | `segment_projection` |
| `replay/layer04_segment.py` (new) | `segment_projection` |
| `services/lab_layer02_timeline.py` | `deprecated_wrapper` after migrate |
| `layers/layer_04/.../replay.py` | `forbidden_split_authority` → delete |
| `Layer04RimPlacementResult.replay_frames` | `deprecated_wrapper` v1 empty tuple |
| `services/lab_replay_timeline_payload.py` | `canonical_owner` (composition only) |

---

### Task 1: L3 event types and replay limits

**Files:**
- Modify: `django_apps/asteroid_lab/replay/event_types.py`
- Modify: `django_apps/asteroid_lab/replay/replay_enums.py`
- Modify: `django_apps/asteroid_lab/replay/replay_limits.py`
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 1: Write failing test**

```python
def test_layer03_event_types_registered() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
        SNAPSHOT_EVENT_TYPES,
        is_registered_event_type,
    )

    for wire in (
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
        EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY,
    ):
        assert wire in SNAPSHOT_EVENT_TYPES
        assert is_registered_event_type(wire)


def test_replay_limits_layer03_top_n_constant() -> None:
    from django_apps.asteroid_lab.replay.replay_limits import (
        LAYER03_REPLAY_TOP_N,
        MAX_LAYER04_REPLAY_SELECTED,
    )

    assert LAYER03_REPLAY_TOP_N == 8
    assert MAX_LAYER04_REPLAY_SELECTED == 32
```

- [ ] **Step 2: Run test — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer03_event_types_registered tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_replay_limits_layer03_top_n_constant -v`

- [ ] **Step 3: Implement constants**

In `event_types.py` after Layer04 block:

```python
EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_BEGIN = "layer03_rim_bundle_scan_begin"
EVENT_TYPE_LAYER03_RIM_BUNDLE_SCAN_COMPLETE = "layer03_rim_bundle_scan_complete"
EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_SUMMARY = "layer03_rim_bundle_pool_summary"
```

Add all three to `SNAPSHOT_EVENT_TYPES` frozenset.

In `replay_enums.py` `ReplayEventType`:

```python
LAYER03_RIM_BUNDLE_SCAN_BEGIN = "layer03_rim_bundle_scan_begin"
LAYER03_RIM_BUNDLE_SCAN_COMPLETE = "layer03_rim_bundle_scan_complete"
LAYER03_RIM_BUNDLE_POOL_SUMMARY = "layer03_rim_bundle_pool_summary"
```

In `replay_limits.py`:

```python
LAYER03_REPLAY_TOP_N = 8
MAX_LAYER04_REPLAY_SELECTED = 32
```

- [ ] **Step 4: Run test — PASS**

- [ ] **Step 5: Commit** (if user requested)

---

### Task 2: `layer02_segment` + assembler skeleton (L2 parity)

**Files:**
- Create: `tests/unit/asteroid_lab/replay/fixtures/replay_assembler_fixtures.py` (see Shared test fixtures above)
- Create: `django_apps/asteroid_lab/replay/layer02_segment.py`
- Create: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`
- Modify: `django_apps/asteroid_lab/replay/lab_timeline_adapter.py` (host `find_reconstruction_complete_source_frame`)
- Modify: `django_apps/asteroid_lab/services/lab_layer02_timeline.py`
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 0: Create `replay_assembler_fixtures.py`** (copy from plan section “Shared test fixtures”; omit `rim_bundle_candidate_set_missing_exterior_plan` until Task 4 observability exists, or stub with `pytest.skip`).

- [ ] **Step 1: Write failing parity test**

```python
def test_layer02_segment_matches_legacy_timeline_dict() -> None:
    from django_apps.asteroid_lab.replay.layer02_segment import (
        build_layer02_exterior_transport_frame,
    )
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_timeline_frame_to_json_dict,
    )
    from django_apps.asteroid_lab.services.lab_layer02_timeline import (
        build_layer02_timeline_frame_dict,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    plan_wire = exterior_plan_wire_for_golden()
    complete = golden_5x5_complete_map()
    source = reconstruction_complete_lab_frame_dict_for_golden()
    legacy = build_layer02_timeline_frame_dict(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete,
    )
    segment = build_layer02_exterior_transport_frame(
        plan_wire=plan_wire,
        source_frame=source,
        complete_map=complete,
    )

    segment_json = replay_timeline_frame_to_json_dict(segment)
    assert segment_json["event_type"] == legacy["event_type"]
    assert segment_json["map_view"]["full_cells"] == legacy["map_view"]["full_cells"]
```

- [ ] **Step 2: Run — FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py::test_layer02_segment_matches_legacy_timeline_dict -v`

- [ ] **Step 3: Move logic**

Copy `build_layer02_timeline_frame_dict` body into `build_layer02_exterior_transport_frame(...) -> ReplayTimelineFrame` using `ReplayEventType.EXTERIOR_TRANSPORT_COMPLETED`, `ReplayPhase.RECONSTRUCTION`, `replay_map_view_is_renderable` helpers from `timeline_dtos` / `timeline_serialization`.

In `lab_layer02_timeline.py`:

```python
def build_layer02_timeline_frame_dict(...):
    from django_apps.asteroid_lab.replay.layer02_segment import (
        build_layer02_exterior_transport_frame,
    )
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_timeline_frame_to_json_dict,
    )

    return replay_timeline_frame_to_json_dict(
        build_layer02_exterior_transport_frame(
            plan_wire=plan_wire,
            source_frame=source_frame,
            complete_map=complete_map,
        )
    )
```

- [ ] **Step 4: Assembler skeleton**

```python
# solver_runtime_assembler.py (skeleton — extend in Tasks 5–6)
def build_solver_runtime_replay_frames(
    *,
    complete_map: ReconstructionCompleteMap,
    lab_frames_before_append: Sequence[Mapping[str, Any]],
    exterior_plan_wire: Mapping[str, Any] | None,
    layer03: RimBundleCandidateSet | None,
    layer04: Layer04RimPlacementResult | None,
) -> list[dict[str, Any]]:
    from django_apps.asteroid_lab.replay.lab_timeline_adapter import (
        find_reconstruction_complete_source_frame,
    )
    from django_apps.asteroid_lab.replay.layer02_segment import (
        build_layer02_exterior_transport_frame,
    )
    from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView
    from django_apps.asteroid_lab.replay.timeline_serialization import (
        replay_map_view_from_json_dict,
        replay_timeline_frame_to_json_dict,
    )

    source = find_reconstruction_complete_source_frame(list(lab_frames_before_append))
    if source is not None:
        current_base_map_view = replay_map_view_from_json_dict(source["map_view"])
    else:
        current_base_map_view = _map_view_from_complete_map(complete_map)

    frames: list[ReplayTimelineFrame] = []
    if exterior_plan_wire is not None:
        l2_frame = build_layer02_exterior_transport_frame(
            plan_wire=exterior_plan_wire,
            source_frame=source,
            complete_map=complete_map if source is None else None,
        )
        frames.append(l2_frame)
        current_base_map_view = l2_frame.map_view

    # Tasks 5–6: L3 segment updates current_base_map_view; L4 receives final current_base_map_view
    del current_base_map_view  # remove when wired

    return [replay_timeline_frame_to_json_dict(fr) for fr in frames]
```

Move `find_reconstruction_complete_source_frame` from `services/lab_layer02_timeline.py` into `replay/lab_timeline_adapter.py`; re-export from `lab_layer02_timeline` for backward compatibility. Implement `_map_view_from_complete_map` in `replay/layer02_segment.py` (shared with L3).

- [ ] **Step 5: Run parity test — PASS**

---

### Task 3: Migrate L4 segment; delete layer `replay.py`

**Files:**
- Create: `django_apps/asteroid_lab/replay/layer04_segment.py`
- Delete: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/replay.py`
- Modify: `django_apps/asteroid_lab/layers/layer_04_rim_bundle_placement/run.py`
- Create: `tests/unit/asteroid_lab/replay/test_layer04_segment.py`
- Modify: `tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py`

- [ ] **Step 1: Port test to `test_layer04_segment.py`**

```python
def test_layer04_segment_emits_begin_selected_complete() -> None:
    from django_apps.asteroid_lab.replay.event_types import (
        EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
        EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
        is_registered_event_type,
    )
    from django_apps.asteroid_lab.replay.layer04_segment import (
        build_layer04_runtime_segment_frames,
    )
    from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
        build_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.test_layer_04_rim_placement import (
        succeeded_probe_at,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        renderable_base_map_view_for_golden,
    )

    placement = build_rim_bundle_placement(succeeded_probe_at((3, 4)))
    base_map_view = renderable_base_map_view_for_golden()
    frames = build_layer04_runtime_segment_frames(
        selected=(placement,),
        rejected=(),
        base_map_view=base_map_view,
    )
    types = [fr.event_type.value for fr in frames]
    assert types[0] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN
    assert EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED in types
    assert types[-1] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE
    assert all(is_registered_event_type(t) for t in types)
    assert all(replay_map_view_is_renderable(fr.map_view) for fr in frames)
```

Implement `build_layer04_runtime_segment_frames(*, selected, rejected, base_map_view: ReplayMapView) -> tuple[ReplayTimelineFrame, ...]` by porting metadata from deleted `replay.py`. **Segment MUST NOT accept `lab_frames` or search prior events.** Cap selected at `MAX_LAYER04_REPLAY_SELECTED` with `metrics={"truncated_selected_replay": True}` on the complete frame when truncated.

- [ ] **Step 2: Update `run.py`**

Remove `from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.replay import build_layer04_replay_frames` and the `replay_frames=build_layer04_replay_frames(...)` call. Pass empty tuple:

```python
return build_layer04_rim_placement_result(
    selected_placements=placements,
    rejected_candidates=rejected,
    provisional_overlay=overlay,
    replay_frames=(),
)
```

Add module comment: runtime timeline frames are built by `replay.solver_runtime_assembler` only.

- [ ] **Step 3: Delete `layers/.../replay.py`; remove test from `test_layer_04_rim_placement.py`**

- [ ] **Step 4: Wire assembler L4 branch (assembler passes `current_base_map_view` only)**

In `build_solver_runtime_replay_frames`, after L3 block:

```python
if layer04 is not None:
    l4_frames = build_layer04_runtime_segment_frames(
        selected=layer04.selected_placements,
        rejected=layer04.rejected_candidates,
        base_map_view=current_base_map_view,
    )
    frames.extend(l4_frames)
```

Do **not** pass `lab_frames_before_append` into `layer04_segment`. PR-A may ship with `layer03=None` and L4 using `current_base_map_view` from L2 or reconstruction only.

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_layer04_segment.py -v`

---

### Task 4: `Layer03Observability` contract

**Files:**
- Create: `django_apps/asteroid_lab/layers/contracts/layer03_observability.py`
- Modify: `django_apps/asteroid_lab/layers/contracts/candidates.py`
- Modify: `django_apps/asteroid_lab/layers/layer_03_rim_mining_bundles/expand.py`
- Test: `tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py`

- [ ] **Step 1: Failing test — factory requires observability**

```python
def test_build_rim_bundle_candidate_set_requires_observability() -> None:
    import pytest
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        Layer03SkipReason,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer03_observability import (
        Layer03Observability,
        build_layer03_observability_for_test,
    )

    obs = build_layer03_observability_for_test(skip_reason=Layer03SkipReason.NONE)
    result = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
        observability=obs,
    )
    assert result.observability.skip_reason is Layer03SkipReason.NONE
```

- [ ] **Step 2: Implement `Layer03Observability` + `build_layer03_observability(...)`**

Helper in observability module:

```python
def select_top_normal_candidates_for_replay(
    normal_candidates: Sequence[RouteProbedBundleCandidate],
    *,
    top_n: int = LAYER03_REPLAY_TOP_N,
) -> tuple[RouteProbedBundleCandidate, ...]:
    ordered = sorted(
        normal_candidates,
        key=lambda e: (
            e.candidate.intrinsic_priority_rank,
            e.candidate.anchor_coord[1],
            e.candidate.anchor_coord[0],
            e.candidate.equivalence_key,
            e.candidate.candidate_id,
        ),
    )
    return tuple(ordered[:top_n])
```

**Circular import guard:** `layer03_observability.py` imports `RouteProbedBundleCandidate` from `candidates.py`; `candidates.py` imports `Layer03Observability` only under `TYPE_CHECKING` or at bottom after class defs — prefer separate file as spec states.

- [ ] **Step 3: Update every `build_rim_bundle_candidate_set(...)` call site** (expand early returns + final return) to pass `observability=build_layer03_observability(...)`.

Run: `python -m pytest tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py -v`

---

### Task 5: `layer03_segment` + assembler L3 frames

**Files:**
- Create: `django_apps/asteroid_lab/replay/layer03_segment.py`
- Modify: `django_apps/asteroid_lab/replay/solver_runtime_assembler.py`
- Test: `tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py`

- [ ] **Step 1: Failing test — L3 begin after L2 when plan present**

```python
def test_assembler_emits_l3_begin_after_l2_when_plan_wire_present() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )
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
    assert types.index("layer03_rim_bundle_scan_begin") > types.index(
        "exterior_transport.completed"
    )
```

Add `rim_bundle_candidate_set_with_observability_for_golden()` to `replay_assembler_fixtures.py` after Task 4 (wraps a real `expand_rim_bundle_candidates` run or minimal factory with `Layer03SkipReason.NONE` and non-empty top-N).

- [ ] **Step 2: Failing test — NO L2 completed when plan None**

```python
def test_assembler_skips_l2_completed_when_exterior_plan_wire_none() -> None:
    from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
        build_solver_runtime_replay_frames,
    )
    from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        reconstruction_complete_lab_frame_dict_for_golden,
        rim_bundle_candidate_set_missing_exterior_plan,
    )

    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=None,
        layer03=rim_bundle_candidate_set_missing_exterior_plan(),
        layer04=None,
    )
    types = [f["event_type"] for f in frames]
    assert "exterior_transport.completed" not in types

    begin = next(f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_begin")
    assert begin["map_view"]["full_cells"]
    assert replay_map_view_is_renderable(
        replay_map_view_from_json_dict(begin["map_view"])
    )

    complete = next(
        f for f in frames if f["event_type"] == "layer03_rim_bundle_scan_complete"
    )
    assert complete["metrics"]["layer03_skip_reason"] == "missing_exterior_connection_plan"
```

Import `replay_map_view_from_json_dict` in the test module.

- [ ] **Step 3: Implement `build_layer03_runtime_segment_frames(*, observability, base_map_view: ReplayMapView) -> tuple[ReplayTimelineFrame, ...]`**

Three frames: begin, complete (`metrics` includes `layer03_skip_reason` string value), pool summary (overlay from `top_normal_candidates`). Assembler sets `current_base_map_view = pool_summary_frame.map_view` after L3.

- [ ] **Step 4: Append L3 frames in assembler after L2 block; update `current_base_map_view` before L4**

```python
if layer03 is not None:
    l3_frames = build_layer03_runtime_segment_frames(
        observability=layer03.observability,
        base_map_view=current_base_map_view,
    )
    frames.extend(l3_frames)
    current_base_map_view = l3_frames[-1].map_view
```

- [ ] **Step 5: Run tests — PASS**

---

### Task 6: Full runtime wire

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_layer02.py`
- Modify: `django_apps/asteroid_lab/services/lab_layer02_timeline.py`

- [ ] **Step 1: Replace `build_layer02_runtime_replay_frames` call**

```python
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)

runtime_replay_frames = build_solver_runtime_replay_frames(
    complete_map=layer01.complete_map,
    lab_frames_before_append=lab_serialized,
    exterior_plan_wire=plan_wire,
    layer03=layer03,
    layer04=layer04,
)
```

- [ ] **Step 2: Deprecation wrapper in `lab_layer02_timeline.py`**

```python
def build_layer02_runtime_replay_frames(...) -> list[dict[str, Any]]:
    """Deprecated: use replay.solver_runtime_assembler.build_solver_runtime_replay_frames."""
    return build_solver_runtime_replay_frames(
        complete_map=complete_map,
        lab_frames_before_append=lab_frames_before_append,
        exterior_plan_wire=plan_wire,
        layer03=None,
        layer04=None,
    )
```

- [ ] **Step 3: Add test wrapper still L2-only when layer03/04 None**

```python
def test_deprecated_layer02_wrapper_omits_l3() -> None:
    from django_apps.asteroid_lab.services.lab_layer02_timeline import (
        build_layer02_runtime_replay_frames,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
        golden_5x5_complete_map,
    )
    from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
        exterior_plan_wire_for_golden,
        reconstruction_complete_lab_frame_dict_for_golden,
    )

    frames = build_layer02_runtime_replay_frames(
        plan_wire=exterior_plan_wire_for_golden(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        complete_map=golden_5x5_complete_map(),
    )
    assert "layer03_rim_bundle_scan_begin" not in [f["event_type"] for f in frames]
```

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_solver_runtime_assembler.py tests/unit/asteroid_lab/test_solver_runtime_rim_stack.py -v`

---

### Task 7: Authority gates + timeline integration

**Files:**
- Create: `tests/unit/asteroid_lab/replay/test_replay_authority_gates.py`
- Create: `tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py`

- [ ] **Step 1: AST gate — no `ReplayTimelineFrame` import in layers**

```python
def test_layers_packages_do_not_import_replay_timeline_frame() -> None:
    import ast
    import pathlib

    root = pathlib.Path("django_apps/asteroid_lab/layers")
    offenders: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if "ReplayTimelineFrame" in {alias.name for alias in node.names}:
                    offenders.append(f"{path}: import from {node.module}")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.endswith("ReplayTimelineFrame"):
                        offenders.append(f"{path}: import {alias.name}")
    assert offenders == []
```

- [ ] **Step 2: Grep gate — no `solver_runtime_replay_frames` literal in layers**

```python
def test_layers_packages_do_not_reference_solver_runtime_replay_frames_key() -> None:
    import pathlib

    root = pathlib.Path("django_apps/asteroid_lab/layers")
    needle = "solver_runtime_replay_frames"
    offenders = [
        str(p)
        for p in root.rglob("*.py")
        if needle in p.read_text(encoding="utf-8")
    ]
    assert offenders == []
```

- [ ] **Step 3: `@pytest.mark.django_db` integration**

After `run_layer02_solver_for_project` (or minimal SolverRun factory with config_json runtime segment), call `build_lab_replay_frames_for_project(project_id, solver_run_id=run_id)` and assert any `f["event_type"] == "layer03_rim_bundle_scan_begin"`.

Use existing asteroid_lab project fixtures pattern from `test_solver_runtime_rim_stack.py` if present.

Run: `python -m pytest tests/unit/asteroid_lab/replay/test_replay_authority_gates.py tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py -v`

---

### Task 8: Doc patches + `replay/__init__.py` exports

**Files:**
- Modify: `django_apps/asteroid_lab/replay/__init__.py`
- Patch: L3/L4 parent specs (short cross-links + “replay owned by central assembler”)

Export `build_solver_runtime_replay_frames` from `replay/__init__.py` optional (avoid bloating `__all__` — services may import submodule directly).

Add to L4 design §1.1 Purpose row: “replay frames via central assembler (not layer package)”.

Add to L3 design §1.3: cross-link central assembler spec.

---

### Task 9: PR gate

```powershell
python -m pytest tests/unit/asteroid_lab/replay/ tests/unit/asteroid_lab/test_lab_replay_timeline_layer03_runtime.py tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py tests/unit/asteroid_lab/layers/test_layer_04_rim_placement.py tests/unit/asteroid_lab/layers/test_layer_03_rim_generation.py -v
python -m ruff check django_apps/asteroid_lab/replay/ django_apps/asteroid_lab/layers/contracts/layer03_observability.py django_apps/asteroid_lab/services/solver_runtime_layer02.py
python -m mypy django_apps/asteroid_lab/replay/solver_runtime_assembler.py django_apps/asteroid_lab/layers/contracts/layer03_observability.py
```

---

## Spec coverage self-review

| Spec § | Task |
|--------|------|
| §1 blocking reunification | 0, 3, 7 |
| §2 Layer03Observability | 4 |
| §2.2 L4 off replay_frames | 3 |
| §3.2 sequence | 5, 6 |
| §3.3 L2 missing plan | 5 Step 2 |
| §3.6 caps | 1, 3, 5 |
| §4 assembler API | 2, 5, 6 |
| §4.4 deprecated wrapper | 6 |
| §5 Task 4 authority tests | 7 |
| §5 parent doc patches | 8 |
| Assembler `current_base_map_view` | Task 2–6 section + Tasks 3–5 |
| Task 0 inventory evidence | Task 0 + Inventory results below |

**Placeholder policy:** No `...` in committed test or production code. Fixture names are defined in `replay_assembler_fixtures.py` before assembler tests run.

---

## Inventory results (fill during Task 0)

| Path / symbol | Classification | Notes |
|---------------|----------------|-------|
| (paste rg output rows here) | | |
| | | |

- [ ] Task 0 table copied to PR description
- [ ] Task 0 table committed in `docs/superpowers/reports/2026-05-28-replay-authority-inventory.md`

---

## Risks

| Risk | Mitigation |
|------|------------|
| `find_reconstruction_complete_source_frame` location | Move to `replay/` in Task 2 to avoid services owning discovery |
| Fixture `to_wire_dict` naming | Read `minimal_l2_plan_for_golden` before Task 2 test |
| Large PR | Optional PR-A / PR-B split above |
| Quarantined timeline tests | Run listed tests; do not `-q` suppressed quarantine without triage |
