# Reconstruction Complete Map DTO — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

## Stale plan warning

**Do not execute** [`2026-05-25-reconstruction-field-cell-capacity-contract.md`](2026-05-25-reconstruction-field-cell-capacity-contract.md) overlay-SoT tasks (`asteroid_field_cells_from_reconstruction(recon)` as capacity numerator). That plan is **stale** per amended spec.

**Authoritative spec:** [`docs/superpowers/specs/2026-05-26-reconstruction-complete-map-dto-design.md`](../specs/2026-05-26-reconstruction-complete-map-dto-design.md)

## Invariant (do not drift)

- **Terrain SoT:** `build_reconstruction_complete_map(cleanup, recon)` → `ReconstructionCompleteMap` only.
- **Forbidden:** public APIs taking `ReconstructionResult` for capacity / `mineable_cells` / field counts; reading replay `full_map` as solver input; stuffing merged cells into `ReconstructionResult.cells`.
- **Unchanged:** RTTP commit semantics, replay-as-input ban, PR-2b committed throughput formula, ×4 per field cell (not ×16 bundle for terrain cap).

**Goal:** Lab capacity, `OptimizationInput.mineable_cells`, and observability field counts match `step4_10` / Cell detail (`asteroid_*_field` on merged map), not sparse overlay (~32 on canon maps).

**Architecture:** New `complete_map.py` factory builds merged display + derived `field_cells` / void topology once; `field_cells.py` public API accepts only `ReconstructionCompleteMap`; solver builds complete map once in `solver_runtime_entry` and threads it through capacity + optimization.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, black, mypy `django_apps config src`

**Branch:** `feat/reconstruction-complete-map-dto` (dedicated worktree recommended)

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/reconstruction/complete_map.py` | `ReconstructionCompleteMap`, `build_reconstruction_complete_map`, private `_field_cells_from_decoded_cells` |
| Modify | `django_apps/asteroid_lab/reconstruction/field_cells.py` | Public `*_from_complete_map`; remove overlay SoT exports |
| Modify | `django_apps/asteroid_lab/reconstruction/acceptance_topology.py` | `acceptance_topology_from_complete_map` / `from_cells` for factory |
| Modify | `django_apps/asteroid_lab/reconstruction/result.py` | Docstring: `.cells` = overlay only |
| Modify | `django_apps/asteroid_lab/reconstruction/confidence.py` | `confirmed_cells` from complete map when `cleanup` passed |
| Modify | `django_apps/asteroid_lab/reconstruction/pipeline.py` | Pass `cleanup` into `_finalize_reconstruction_result` |
| Modify | `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py` | Envelope/observability take `ReconstructionCompleteMap` |
| Modify | `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | Required `cleanup`; build complete map |
| Modify | `django_apps/asteroid_lab/services/solver_runtime_entry.py` | Build complete map once; thread through |
| Create | `tests/unit/asteroid_lab/test_complete_map.py` | Factory parity, overlay ≪ complete on canon fixture |
| Modify | `tests/unit/asteroid_lab/test_field_cells.py` | Complete-map API; overlay helper test-only |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py` | Pass `complete_map` |
| Modify | `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | `cleanup` + `complete_map.field_cells` |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` | Compare vs `complete_map.field_cells` |
| Modify | `tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py` | Complete-map confirmed set |
| Modify | `tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py` | `_optimization_input_from_fixture_line` passes cleanup |
| Modify | `tests/unit/asteroid_lab/test_throughput_target.py` | Expect higher recon max when fixture has many fields |
| Modify | `docs/superpowers/plans/2026-05-25-reconstruction-field-cell-capacity-contract.md` | Banner: **STALE — superseded by 2026-05-26 plan** |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/reconstruction-complete-map-dto
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py -v --tb=short
```

Expected: PASS (records current overlay-based behavior before contract fix).

- [ ] **Step 3: Mark stale plan**

Add at top of `docs/superpowers/plans/2026-05-25-reconstruction-field-cell-capacity-contract.md` after the header block:

```markdown
> **STALE (2026-05-26):** Superseded by [`2026-05-26-reconstruction-complete-map-dto.md`](2026-05-26-reconstruction-complete-map-dto.md). Do not implement overlay `recon.cells` SoT steps below.
```

---

### Task 1: `ReconstructionCompleteMap` factory (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/reconstruction/complete_map.py`
- Create: `tests/unit/asteroid_lab/test_complete_map.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_complete_map.py`:

```python
"""Reconstruction-complete map factory — merged display SoT."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import snapshot_summary_from_rows
from django_apps.asteroid_lab.reconstruction.display_map import full_map_rows_from_reconstruction


def _canon_cleanup_recon():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return cleanup, recon


def test_build_complete_map_cells_equal_merged_display() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    expected = merged_display_cells_from_reconstruction(cleanup, recon)
    assert complete.cells == expected


def test_overlay_field_count_less_than_complete_on_canon_fixture() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    overlay_n = overlay_field_cell_count(recon)
    complete_n = len(complete.field_cells)
    assert overlay_n < complete_n
    assert complete_n >= 50


def test_complete_field_count_matches_full_map_row_summary() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    rows = full_map_rows_from_reconstruction(cleanup, recon)
    summary = snapshot_summary_from_rows(rows)
    assert len(complete.field_cells) == int(summary["field_count"])
    assert complete.shape_field_cell_count + complete.fluid_field_cell_count == int(
        summary["field_count"]
    )


def test_complete_map_is_frozen_dto() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    assert isinstance(complete, ReconstructionCompleteMap)
    assert complete.coord_frame == recon.coord_frame
```

- [ ] **Step 2: Run tests — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py -v --tb=short
```

Expected: FAIL — `ModuleNotFoundError: complete_map` or missing `build_reconstruction_complete_map`.

- [ ] **Step 3: Implement `complete_map.py`**

Create `django_apps/asteroid_lab/reconstruction/complete_map.py`:

```python
"""Reconstruction-complete map DTO and sole terrain SoT factory."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from django_apps.asteroid_lab.cleanup.result import CleanupResult
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_decoded_cells,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_SHAPE_FIELD = "asteroid_shape_field"
_FLUID_FIELD = "asteroid_fluid_field"


def _field_cells_from_decoded_cells(
    cells: Sequence[DecodedCellDTO],
    *,
    coord_frame: CoordFrame,
) -> frozenset[Coord]:
    if coord_frame == CoordFrame.WORLD_RAW:
        msg = "WORLD_RAW complete map field cells not implemented"
        raise ValueError(msg)
    out: set[Coord] = set()
    for cell in cells:
        if cell.cell_kind not in ASTEROID_FIELD_KINDS:
            continue
        out.add((cell.x, cell.y))
    return frozenset(out)


def _count_by_resource(cells: Sequence[DecodedCellDTO]) -> dict[str, int]:
    counts = {"shape": 0, "fluid": 0}
    for cell in cells:
        if cell.cell_kind == _SHAPE_FIELD:
            counts["shape"] += 1
        elif cell.cell_kind == _FLUID_FIELD:
            counts["fluid"] += 1
    return counts


def overlay_field_cell_count(recon: ReconstructionResult) -> int:
    """Overlay-only count for contract tests (not terrain SoT)."""

    return len(_field_cells_from_decoded_cells(recon.cells, coord_frame=recon.coord_frame))


@dataclass(frozen=True, slots=True)
class ReconstructionCompleteMap:
    """Merged cleanup structural map + reconstruction overlay."""

    cells: tuple[DecodedCellDTO, ...]
    field_cells: frozenset[Coord]
    shape_field_cell_count: int
    fluid_field_cell_count: int
    external_void_cells: frozenset[Coord]
    coord_frame: CoordFrame


def build_reconstruction_complete_map(
    *,
    cleanup: CleanupResult,
    recon: ReconstructionResult,
) -> ReconstructionCompleteMap:
    """Sole entry point for reconstruction-complete terrain SoT."""

    cells = merged_display_cells_from_reconstruction(cleanup, recon)
    frame = recon.coord_frame
    field_cells = _field_cells_from_decoded_cells(cells, coord_frame=frame)
    by_resource = _count_by_resource(cells)
    topo = acceptance_topology_from_decoded_cells(cells, field_cells=field_cells, coord_frame=frame)
    return ReconstructionCompleteMap(
        cells=cells,
        field_cells=field_cells,
        shape_field_cell_count=by_resource["shape"],
        fluid_field_cell_count=by_resource["fluid"],
        external_void_cells=topo.external_void_cells,
        coord_frame=frame,
    )


__all__ = [
    "ReconstructionCompleteMap",
    "build_reconstruction_complete_map",
    "overlay_field_cell_count",
]
```

- [ ] **Step 4: Add `acceptance_topology_from_decoded_cells` stub in failing state**

In `acceptance_topology.py`, add (minimal for Task 1 — full wiring in Task 2):

```python
def acceptance_topology_from_decoded_cells(
    cells: Sequence[DecodedCellDTO],
    *,
    field_cells: frozenset[Coord],
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> AcceptanceTopology:
    by_coord = _cells_by_topology_coord(tuple(cells), coord_frame=coord_frame)
    all_coords = frozenset(by_coord)
    asteroid_bbox = bbox_from_coords(field_cells if field_cells else all_coords)
    route_domain_bbox = expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)
    external_void = frozenset(c for c in cells_in_bbox(route_domain_bbox) if c not in all_coords)
    return AcceptanceTopology(mineable_cells=field_cells, external_void_cells=external_void)
```

Export in `__all__`.

- [ ] **Step 5: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py -v --tb=short
```

Expected: PASS

- [ ] **Step 6: Ruff**

```powershell
python -m ruff check django_apps/asteroid_lab/reconstruction/complete_map.py django_apps/asteroid_lab/reconstruction/acceptance_topology.py tests/unit/asteroid_lab/test_complete_map.py
```

---

### Task 2: `field_cells.py` — complete-map-only public API

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/field_cells.py`
- Modify: `tests/unit/asteroid_lab/test_field_cells.py`

- [ ] **Step 1: Rewrite failing tests to use `ReconstructionCompleteMap`**

Replace imports and tests — example transport exclusion test:

```python
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_complete_map,
    count_asteroid_field_cells_by_resource,
)
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
# ... use minimal inline cleanup+recon OR build ReconstructionCompleteMap manually for unit cases:

def _complete_map_from_cells(*cells: DecodedCellDTO) -> ReconstructionCompleteMap:
    """Minimal complete map when cleanup merge not needed."""
    frame = CoordFrame.ISLAND_RAW
    field_cells = frozenset(
        (c.x, c.y) for c in cells if c.cell_kind in ASTEROID_FIELD_KINDS
    )
    by = count from cells inline
    return ReconstructionCompleteMap(
        cells=cells,
        field_cells=field_cells,
        shape_field_cell_count=...,
        fluid_field_cell_count=...,
        external_void_cells=frozenset(),
        coord_frame=frame,
    )
```

Prefer a test helper `tests/support/reconstruction_complete_map_fixtures.py` with `_minimal_complete_map(*cells)` to avoid duplicating DTO construction in every test.

Remove `test_acceptance_topology_mineable_equals_field_cells` from this file (move to Task 3).

- [ ] **Step 2: Implement `field_cells.py`**

```python
def asteroid_field_cells_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> frozenset[Coord]:
    return complete_map.field_cells


def count_asteroid_field_cells_by_resource(
    complete_map: ReconstructionCompleteMap,
) -> dict[str, int]:
    return {
        "shape": complete_map.shape_field_cell_count,
        "fluid": complete_map.fluid_field_cell_count,
    }


def detect_primary_resource_kind(complete_map: ReconstructionCompleteMap) -> str:
    if complete_map.fluid_field_cell_count > complete_map.shape_field_cell_count:
        return "fluid"
    return "shape"
```

Remove `asteroid_field_cells_from_reconstruction` from `__all__` (grep repo; keep thin deprecated wrapper only if many call sites remain mid-PR — **prefer delete** and fix call sites in same PR).

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_field_cells.py -v --tb=short
```

---

### Task 3: Acceptance topology from complete map

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/acceptance_topology.py`
- Modify: `tests/unit/asteroid_lab/test_field_cells.py` or add `test_acceptance_topology_complete_map.py`

- [ ] **Step 1: Add `acceptance_topology_from_complete_map`**

```python
def acceptance_topology_from_complete_map(
    complete_map: ReconstructionCompleteMap,
) -> AcceptanceTopology:
    return AcceptanceTopology(
        mineable_cells=complete_map.field_cells,
        external_void_cells=complete_map.external_void_cells,
    )
```

- [ ] **Step 2: Change `acceptance_topology_from_reconstruction`**

Document as **overlay/diagnostic only**; implementation may delegate to overlay field count for confidence internals, but **must not** be called from capacity/optimization paths after Task 4–5.

Add test:

```python
def test_acceptance_topology_from_complete_map_matches_field_cells() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    topo = acceptance_topology_from_complete_map(complete)
    assert topo.mineable_cells == complete.field_cells
```

---

### Task 4: Capacity + observability consume `ReconstructionCompleteMap`

**Files:**
- Modify: `django_apps/asteroid_lab/services/reconstruction_capacity_summary.py`
- Modify: `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py`

- [ ] **Step 1: Update failing tests**

Change helpers to build `complete_map`:

```python
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map

def test_observability_uses_complete_field_counts():
    # use canon fixture or _complete_map_from_cells with 5 shape fields
    obs = build_reconstruction_observability(recon=recon, complete_map=complete)
    assert obs["asteroid_field_cell_count"] == complete.shape_field_cell_count + complete.fluid_field_cell_count
```

- [ ] **Step 2: Change signatures**

```python
def build_reconstruction_capacity_summary(
    *,
    complete_map: ReconstructionCompleteMap,
    resource_kind: str,
    platform_count: int | None = None,
) -> dict[str, Any]:
    if platform_count is None:
        platform_count = (
            complete_map.shape_field_cell_count
            if resource_kind == "shape"
            else complete_map.fluid_field_cell_count
        )
    ...

def build_reconstruction_capacity_envelope(
    *,
    complete_map: ReconstructionCompleteMap,
) -> dict[str, Any]:
    by_resource = count_asteroid_field_cells_by_resource(complete_map)
    ...

def build_reconstruction_observability(
    *,
    recon: ReconstructionResult,
    complete_map: ReconstructionCompleteMap,
) -> dict[str, Any]:
    topo = acceptance_topology_from_complete_map(complete_map)
    obs = {
        "cell_count": len(recon.cells),
        "display_cell_count": len(complete_map.cells),
        "asteroid_field_cell_count": len(complete_map.field_cells),
        ...
    }
```

Remove imports of `asteroid_field_cells_from_reconstruction`.

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py -v --tb=short
```

---

### Task 5: `optimization_input_from_reconstruction` requires `cleanup`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Modify: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`
- Modify: `tests/unit/asteroid_lab/test_optimization_input_coord_frame.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py`
- Modify: other tests calling `optimization_input_from_reconstruction` without cleanup (grep)

- [ ] **Step 1: Change adapter signature**

```python
def optimization_input_from_reconstruction(
    result: ReconstructionResult,
    *,
    cleanup: CleanupResult,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
    catalog_slice: BuildingCatalogSlice | None = None,
) -> OptimizationInput:
    complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=result)
    mineable = complete_map.field_cells
    external_void = complete_map.external_void_cells
    by_coord = _cells_by_coord(complete_map.cells)
    ...
```

- [ ] **Step 2: Update fixture helper**

In `test_rttp_reconstruction_fixture_e2e.py`:

```python
def _optimization_input_from_fixture_line(line_index: int) -> OptimizationInput:
    ...
    return optimization_input_from_reconstruction(recon, cleanup=cleanup, ...)
```

- [ ] **Step 3: Fix all unit tests**

Every `optimization_input_from_reconstruction(ReconstructionResult(...))` needs a minimal `CleanupResult` or uses deconstruct+recon path.

Add regression test:

```python
def test_mineable_cells_equal_complete_map_field_cells():
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    inp = optimization_input_from_reconstruction(recon, cleanup=cleanup, catalog_slice=...)
    assert inp.mineable_cells == complete.field_cells
    assert len(inp.mineable_cells) > overlay_field_cell_count(recon)
```

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py -v --tb=short
```

---

### Task 6: Pipeline confidence + `ReconstructionResult` docstring

**Files:**
- Modify: `django_apps/asteroid_lab/reconstruction/result.py`
- Modify: `django_apps/asteroid_lab/reconstruction/confidence.py`
- Modify: `django_apps/asteroid_lab/reconstruction/pipeline.py`
- Modify: `tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py`

- [ ] **Step 1: Docstring on `ReconstructionResult.cells`**

```python
class ReconstructionResult:
    """Output of reconstruction pipeline.

    ``cells`` is the reconstruction OVERLAY (sparse replaces), not the complete map.
    Use :func:`build_reconstruction_complete_map` for terrain/capacity/mineable SoT.
    """
    cells: tuple[DecodedCellDTO, ...]  # overlay only
```

- [ ] **Step 2: `apply_confidence_to_result` optional cleanup**

```python
def apply_confidence_to_result(
    result: ReconstructionResult,
    *,
    wall_coords: Iterable[Coord],
    interior_patch_coords: Iterable[Coord],
    cleanup: CleanupResult | None = None,
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> ReconstructionResult:
    ...
    if cleanup is not None:
        complete = build_reconstruction_complete_map(cleanup=cleanup, recon=result)
        confirmed = complete.field_cells
        external_void = complete.external_void_cells
    else:
        # unit tests without cleanup only
        confirmed = _field_cells_from_decoded_cells(result.cells, ...)
        external_void = acceptance_topology_from_reconstruction(result).external_void_cells
```

- [ ] **Step 3: `_finalize_reconstruction_result` passes cleanup**

Update callers at `pipeline.py:233` and `:656` to pass `cleanup` from `run_topology_reconstruction` scope.

- [ ] **Step 4: Run confidence tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py -v --tb=short
```

---

### Task 7: `solver_runtime_entry` — build once, thread through

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`

- [ ] **Step 1: Wire complete map**

After `cleanup, recon = run_reconstruction_for_map_input(...)`:

```python
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map

complete_map = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
opt_inp = optimization_input_from_reconstruction(
    recon,
    cleanup=cleanup,
    coord_frame=...,
    catalog_slice=catalog_slice,
)
capacity_env = build_reconstruction_capacity_envelope(complete_map=complete_map)
...
reconstruction_observability=build_reconstruction_observability(
    recon=recon,
    complete_map=complete_map,
),
```

- [ ] **Step 2: Run solver lab summary tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_lab_summary.py tests/unit/asteroid_lab/test_throughput_target.py -v --tb=short
```

Update throughput expectations where reconstruction max rises (intentional per spec).

---

### Task 8: Fixture contract + integration grep cleanup

**Files:**
- Modify: `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py`
- Grep: `asteroid_field_cells_from_reconstruction` / `build_reconstruction_capacity_envelope(recon=`

- [ ] **Step 1: Fixture contract uses complete map**

```python
complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
field_cells = complete.field_cells
assert topo.mineable_cells <= field_cells  # or equality after adapter change
```

- [ ] **Step 2: Grep — zero overlay SoT in production code**

```powershell
rg "asteroid_field_cells_from_reconstruction|build_reconstruction_capacity_envelope\(.*recon=" django_apps --glob "*.py"
```

Expected: no matches in `django_apps/` (tests may keep overlay helper name).

---

### Task 9: Full gate + docs

**Files:**
- Modify: `documents/ai/current_plan.md` (queue line when PR opens)

- [ ] **Step 1: Asteroid lab unit slice**

```powershell
python -m pytest tests/unit/asteroid_lab/test_complete_map.py tests/unit/asteroid_lab/test_field_cells.py tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py -v --tb=short
```

- [ ] **Step 2: PR full gate**

```powershell
powershell -File scripts/test_full.ps1
python -m ruff check .
python -m mypy django_apps config src
python -m black --check .
```

- [ ] **Step 3: Manual regression (Run Solver)**

Re-run solver on map with large field blob; Lab must show `asteroid_field_cell_count` >> overlay-only 32 and theoretical max scaled accordingly.

---

## Plan self-review (2026-05-26)

| Spec requirement | Task |
|------------------|------|
| `ReconstructionCompleteMap` DTO | Task 1 |
| `build_reconstruction_complete_map` sole factory | Task 1, 7 |
| `field_cells` public API only `complete_map` | Task 2 |
| Capacity / observability / optimization use complete map | Tasks 4, 5, 7 |
| Overlay forbidden for SoT | Tasks 2, 5, 8 |
| Replay parity (field_count) | Task 1 `test_complete_field_count_matches_full_map_row_summary` |
| `ReconstructionResult.cells` documented overlay | Task 6 |
| No silent B / no replay readback | Invariant + Task 7 |
| Follow-up rename out of scope | Non-goals in header |

Placeholder scan: no TBD steps.

Type consistency: `ReconstructionCompleteMap`, `build_reconstruction_complete_map`, `asteroid_field_cells_from_complete_map` used consistently.

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-26-reconstruction-complete-map-dto.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute in this session with executing-plans checkpoints  

Which approach do you want?
