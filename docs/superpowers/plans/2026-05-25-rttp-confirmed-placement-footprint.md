# RTTP Confirmed Placement Footprint — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project committed RTTP bundle footprints into Lab replay overlay rows so miners/extensions render with correct sprites (not belt-inferred), without changing `incremental_commit` or persistence.

**Architecture:** Add pure `placement_overlay_projection.py` under `optimization/materialization/`; `rttp_replay_diagnostics.py` calls it for candidate/selection/commit payloads. Wire rows use `cell_kind` + `tile_type` SoT, `transport_kind=none` on equipment, `overlay_semantic_kind` for replay metadata only.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Spec:** [`docs/superpowers/specs/2026-05-26-rttp-confirmed-placement-footprint-design.md`](../specs/2026-05-26-rttp-confirmed-placement-footprint-design.md)

**Branch (recommended):** `fix/rttp-placement-footprint-overlay`

**Plan gate:** Conditional approval cleared 2026-05-25 (review corrections applied below).

### Review corrections (MUST before execution)

| # | Correction | Status |
|---|------------|--------|
| 1 | Route rows keep legacy `kind="route.committed_path"`; `cell_kind` = `space_belt` / `space_pipe` separately | Applied in Task 1 snippet |
| 2 | Remove broken `equipment_coords` duplicate line from snippet | Applied |
| 3 | `build_commit_replay_payload` → `(payload, diag)` tuple; **all** call sites unpack | Applied in Task 2 |
| 4 | Import boundary test uses explicit `Path` list | Applied in Task 3 |

**PR scope note:** Macro commit uses `build_macro_commit_replay_payload` only (`pipeline.py` macro path). **Macro placement footprint overlay is deferred** unless `macro_only` regression explicitly fails this PR's narrow gate.

### Wire: `kind` vs `cell_kind` (Lab + legacy tests)

| Row type | `kind` (legacy replay / tests) | `cell_kind` (Lab sprite SoT) |
|----------|-------------------------------|------------------------------|
| Route | `route.committed_path` | `space_belt` or `space_pipe` |
| Extractor | `placement.*_extractor` semantic | `shape_miner` / `fluid_miner` |
| Extension | `placement.*_extension` semantic | `shape_miner_extension` / … |
| Output stub | `placement.*_output_stub` semantic | `space_belt` / `space_pipe` |

Transport wire (both fields on route/stub; equipment uses `none` + empty `transport`):

```python
# equipment
"transport_kind": "none", "transport": ""
# route / stub
"transport_kind": "shape_belt", "transport": "shape_belt"  # or fluid_pipe pair
```

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/optimization/materialization/__init__.py` | Package export |
| Create | `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py` | Overlay row builders + merge/diagnostics |
| Create | `tests/unit/asteroid_lab/test_placement_overlay_projection.py` | Projector unit tests |
| Modify | `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py` | Wire payloads; extend commit payload signature |
| Modify | `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py` | Regression + new overlay contract tests |
| Modify | `django_apps/asteroid_lab/optimization/pipeline.py` | Merge overlap/visibility metrics into commit `metrics_json` |
| Modify | `docs/superpowers/specs/2026-05-26-rttp-confirmed-placement-footprint-design.md` | Already polished 2026-05-25 |

**Must NOT modify:** `incremental_commit.py`, export/persist modules, `asteroid_miner_layout_lab.js` (unless tests prove JS gap — spec says no JS change expected).

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b fix/rttp-placement-footprint-overlay
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py -v --tb=short
```

Expected: PASS (records behavior before footprint rows).

---

### Task 1: `placement_overlay_projection` module (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/optimization/materialization/__init__.py`
- Create: `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py`
- Create: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`

- [ ] **Step 1: Write failing projector tests**

Create `tests/unit/asteroid_lab/test_placement_overlay_projection.py`:

```python
"""Placement overlay projection — Lab wire rows from BundleCandidate (PR-1)."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection import (
    PlacementOverlayDiagnostics,
    build_candidate_placement_overlay_rows,
    build_confirmed_placement_overlay_rows,
    build_selected_placement_overlay_rows,
    merge_overlay_rows_by_priority,
)


def _pattern(pattern_id: str) -> BundlePattern:
    for row in build_pattern_library():
        if row.pattern_id == pattern_id:
            return row
    raise AssertionError(pattern_id)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _candidate(
    anchor: tuple[int, int] = (5, 5),
    *,
    pattern_id: str = "lin_e_len1",
) -> BundleCandidate:
    pattern = _pattern(pattern_id)
    occupied = frozenset(_translate(anchor, o) for o in pattern.occupied_offsets)
    output_stub = _translate(anchor, pattern.output_stub_offset)
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=3,
        reachable=True,
        catalog_placement_ref=CatalogPlacementRef(
            canonical_id="ExtractorDefaultInternalVariant",
            anchor_coord=anchor,
            rotation=CardinalDirection.E,
        ),
    )


def test_confirmed_rows_use_miner_cell_kind_and_none_transport() -> None:
    cand = _candidate()
    rows, diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset({(7, 5), (8, 5)}),
    )
    miners = [r for r in rows if r.get("cell_kind") == "shape_miner"]
    assert len(miners) == 1
    assert miners[0]["transport_kind"] == "none"
    assert miners[0]["tile_type"] == "Layout_ShapeMiner"
    assert miners[0]["overlay_semantic_kind"] == "placement.confirmed_extractor"
    assert miners[0].get("commit_state") == "confirmed"
    assert diag.visible_miner_cell_count == 1
    assert diag.visible_extension_cell_count == 1


def test_candidate_rows_omit_commit_state() -> None:
    cand = _candidate()
    rows = build_candidate_placement_overlay_rows((cand,))
    assert all("commit_state" not in r for r in rows)
    assert any(r["overlay_semantic_kind"] == "placement.candidate_extractor" for r in rows)


def test_selected_rows_omit_commit_state() -> None:
    cand = _candidate()
    rows = build_selected_placement_overlay_rows((cand.candidate_id,), {cand.candidate_id: cand})
    assert all("commit_state" not in r for r in rows)
    assert all(r.get("transport_kind") == "none" for r in rows if r["cell_kind"] == "shape_miner")


def test_merge_prefers_placement_over_route() -> None:
    placement = [{"x": 1, "y": 0, "cell_kind": "shape_miner", "priority": 3}]
    route = [{"x": 1, "y": 0, "cell_kind": "space_belt", "priority": 1}]
    merged = merge_overlay_rows_by_priority(placement + route)
    assert len(merged) == 1
    assert merged[0]["cell_kind"] == "shape_miner"


def test_overlap_emits_metrics_json_fields() -> None:
    cand = _candidate(anchor=(5, 5))
    overlap_coord = next(iter(cand.occupied_cells))
    rows, diag = build_confirmed_placement_overlay_rows(
        committed_ids=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
        reserved_route_cells=frozenset({overlap_coord}),
    )
    assert diag.placement_route_overlap_warning_count >= 1
    assert overlap_coord in diag.placement_route_overlap_warning_coords
    assert any(r["cell_kind"] == "shape_miner" for r in rows)
```

- [ ] **Step 2: Run tests to verify they fail**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
```

Expected: FAIL (`ModuleNotFoundError` or import error).

- [ ] **Step 3: Implement minimal projector**

Create `django_apps/asteroid_lab/optimization/materialization/__init__.py`:

```python
from django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection import (
    PlacementOverlayDiagnostics,
    build_candidate_placement_overlay_rows,
    build_confirmed_placement_overlay_rows,
    build_selected_placement_overlay_rows,
    merge_overlay_rows_by_priority,
)

__all__ = [
    "PlacementOverlayDiagnostics",
    "build_candidate_placement_overlay_rows",
    "build_confirmed_placement_overlay_rows",
    "build_selected_placement_overlay_rows",
    "merge_overlay_rows_by_priority",
]
```

Create `placement_overlay_projection.py` with:

```python
"""Lab replay overlay projection for RTTP bundle footprints (read-only, PR-1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection, CatalogPlacementRef
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

_OUTPUT_DIR_TO_ROTATION: dict[str, int] = {"E": 0, "S": 1, "W": 2, "N": 3}
_CARDINAL_TO_ROTATION: dict[CardinalDirection, int] = {
    CardinalDirection.E: 0,
    CardinalDirection.S: 1,
    CardinalDirection.W: 2,
    CardinalDirection.N: 3,
}

_ROW_PRIORITY: dict[str, int] = {
    "shape_miner": 30,
    "fluid_miner": 30,
    "shape_miner_extension": 30,
    "fluid_miner_extension": 30,
    "space_belt": 20,
    "space_pipe": 20,
}


@dataclass(frozen=True, slots=True)
class PlacementOverlayDiagnostics:
    visible_miner_cell_count: int
    visible_extension_cell_count: int
    placement_route_overlap_warning_count: int
    placement_route_overlap_warning_coords: tuple[Coord, ...]


def _equipment_kinds(transport_kind: TransportKind) -> tuple[str, str, str, str]:
    if transport_kind is TransportKind.FLUID_PIPE:
        return (
            "fluid_miner",
            "fluid_miner_extension",
            "Layout_FluidMiner",
            "Layout_FluidMinerExtension",
        )
    return (
        "shape_miner",
        "shape_miner_extension",
        "Layout_ShapeMiner",
        "Layout_ShapeMinerExtension",
    )


def _transport_channel(transport_kind: TransportKind) -> tuple[str, str, str]:
    if transport_kind is TransportKind.FLUID_PIPE:
        return ("space_pipe", "SpacePipe_Forward", "fluid_pipe")
    return ("space_belt", "SpaceBelt_Forward", "shape_belt")


def _rotation_for_candidate(candidate: BundleCandidate) -> int:
    ref = candidate.catalog_placement_ref
    if ref is not None:
        return _CARDINAL_TO_ROTATION[ref.rotation]
    return _OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0)


def _base_row(
    coord: Coord,
    *,
    kind: str | None,
    cell_kind: str,
    tile_type: str,
    transport_kind: str,
    overlay_semantic_kind: str,
    rotation: int,
    candidate_id: str,
    commit_state: str | None = None,
) -> dict[str, Any]:
    wire_kind = kind if kind is not None else overlay_semantic_kind
    wire_transport = "" if transport_kind == "none" else transport_kind
    row: dict[str, Any] = {
        "x": int(coord[0]),
        "y": int(coord[1]),
        "kind": wire_kind,
        "cell_kind": cell_kind,
        "tile_type": tile_type,
        "sprite_identifier": tile_type,
        "transport_kind": transport_kind,
        "transport": wire_transport,
        "rotation": rotation,
        "overlay_semantic_kind": overlay_semantic_kind,
        "candidate_id": candidate_id,
    }
    if commit_state is not None:
        row["commit_state"] = commit_state
    return row


def _rows_for_candidate(
    candidate: BundleCandidate,
    *,
    extractor_semantic: str,
    extension_semantic: str,
    stub_semantic: str,
    commit_state: str | None,
) -> list[dict[str, Any]]:
    miner_ck, ext_ck, miner_tt, ext_tt = _equipment_kinds(candidate.transport_kind)
    belt_ck, belt_tt, belt_tk = _transport_channel(candidate.transport_kind)
    rotation = _rotation_for_candidate(candidate)
    anchor = candidate.anchor_coord
    pattern = candidate.pattern

    def at(offset: Coord) -> Coord:
        return (anchor[0] + offset[0], anchor[1] + offset[1])

    rows: list[dict[str, Any]] = []
    rows.append(
        _base_row(
            at(pattern.extractor_offset),
            kind=extractor_semantic,
            cell_kind=miner_ck,
            tile_type=miner_tt,
            transport_kind="none",
            overlay_semantic_kind=extractor_semantic,
            rotation=rotation,
            candidate_id=candidate.candidate_id,
            commit_state=commit_state,
        )
    )
    for offset in pattern.extension_offsets:
        rows.append(
            _base_row(
                at(offset),
                kind=extension_semantic,
                cell_kind=ext_ck,
                tile_type=ext_tt,
                transport_kind="none",
                overlay_semantic_kind=extension_semantic,
                rotation=rotation,
                candidate_id=candidate.candidate_id,
                commit_state=commit_state,
            )
        )
    rows.append(
        _base_row(
            candidate.output_stub,
            kind=stub_semantic,
            cell_kind=belt_ck,
            tile_type=belt_tt,
            transport_kind=belt_tk,
            overlay_semantic_kind=stub_semantic,
            rotation=_OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0),
            candidate_id=candidate.candidate_id,
            commit_state=commit_state,
        )
    )
    return rows


def _route_rows(
    coords: frozenset[Coord],
    *,
    transport_kind: TransportKind,
    candidate_id: str = "",
) -> list[dict[str, Any]]:
    belt_ck, belt_tt, belt_tk = _transport_channel(transport_kind)
    return [
        _base_row(
            coord,
            kind="route.committed_path",
            cell_kind=belt_ck,
            tile_type=belt_tt,
            transport_kind=belt_tk,
            overlay_semantic_kind="route.committed_path",
            rotation=0,
            candidate_id=candidate_id,
        )
        for coord in sorted(coords, key=lambda c: (c[1], c[0]))
    ]


def merge_overlay_rows_by_priority(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_coord: dict[Coord, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        coord = (int(row["x"]), int(row["y"]))
        ck = str(row.get("cell_kind") or row.get("kind") or "")
        priority = _ROW_PRIORITY.get(ck, int(row.get("priority", 0)))
        existing = by_coord.get(coord)
        if existing is None or priority > _ROW_PRIORITY.get(
            str(existing.get("cell_kind") or existing.get("kind") or ""),
            0,
        ):
            by_coord[coord] = row
    return list(by_coord.values())


def build_candidate_placement_overlay_rows(
    candidates: Sequence[BundleCandidate],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate in candidates:
        out.extend(
            _rows_for_candidate(
                candidate,
                extractor_semantic="placement.candidate_extractor",
                extension_semantic="placement.candidate_extension",
                stub_semantic="placement.candidate_output_stub",
                commit_state=None,
            )
        )
    return out


def build_selected_placement_overlay_rows(
    commit_order: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for cid in commit_order:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        out.extend(
            _rows_for_candidate(
                candidate,
                extractor_semantic="placement.selected_extractor",
                extension_semantic="placement.selected_extension",
                stub_semantic="placement.selected_output_stub",
                commit_state=None,
            )
        )
    return out


def build_confirmed_placement_overlay_rows(
    *,
    committed_ids: Sequence[str],
    candidates_by_id: Mapping[str, BundleCandidate],
    reserved_route_cells: frozenset[Coord],
) -> tuple[list[dict[str, Any]], PlacementOverlayDiagnostics]:
    placement_rows: list[dict[str, Any]] = []
    route_coords: set[Coord] = set(reserved_route_cells)
    overlap_coords: list[Coord] = []
    miner_count = 0
    ext_count = 0

    for cid in committed_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is None:
            continue
        bundle_rows = _rows_for_candidate(
            candidate,
            extractor_semantic="placement.confirmed_extractor",
            extension_semantic="placement.confirmed_extension",
            stub_semantic="placement.confirmed_output_stub",
            commit_state="confirmed",
        )
        equipment_coords = candidate.occupied_cells
        for coord in equipment_coords:
            if coord in reserved_route_cells:
                overlap_coords.append(coord)
        miner_count += 1
        ext_count += len(candidate.pattern.extension_offsets)
        placement_rows.extend(bundle_rows)
        route_coords -= candidate.occupied_cells
        route_coords.discard(candidate.output_stub)

    transport = (
        candidates_by_id[committed_ids[0]].transport_kind
        if committed_ids and committed_ids[0] in candidates_by_id
        else TransportKind.SHAPE_BELT
    )
    route_rows = _route_rows(frozenset(route_coords), transport_kind=transport)
    merged = merge_overlay_rows_by_priority(placement_rows + route_rows)

    diag = PlacementOverlayDiagnostics(
        visible_miner_cell_count=miner_count,
        visible_extension_cell_count=ext_count,
        placement_route_overlap_warning_count=len(overlap_coords),
        placement_route_overlap_warning_coords=tuple(sorted(set(overlap_coords))),
    )
    return merged, diag
```

- [ ] **Step 3b: Add route `kind` regression in projector tests**

Append to `test_placement_overlay_projection.py`:

```python
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection import (
    _route_rows,
)


def test_route_rows_keep_legacy_kind_route_committed_path() -> None:
    rows = _route_rows(frozenset({(2, 0)}), transport_kind=TransportKind.SHAPE_BELT)
    assert rows[0]["kind"] == "route.committed_path"
    assert rows[0]["cell_kind"] == "space_belt"
    assert rows[0]["transport_kind"] == "shape_belt"
    assert rows[0]["transport"] == "shape_belt"
```

Export `_route_rows` only for tests if preferred; otherwise test via `build_confirmed_placement_overlay_rows` and assert route row `kind`.

- [ ] **Step 4: Run projector tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 5: Ruff on new module**

```powershell
python -m ruff check django_apps/asteroid_lab/optimization/materialization tests/unit/asteroid_lab/test_placement_overlay_projection.py
```

Expected: PASS.

---

### Task 2: Wire `rttp_replay_diagnostics.py`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py`

- [ ] **Step 1: Write failing integration tests in replay diagnostics**

Append to `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py` (reuse `_bundle_candidate` helper — copy minimal helper from `test_rttp_greedy_regret.py` or import shared fixture):

```python
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def _pattern_by_id(pattern_id: str):
    for pattern in build_pattern_library():
        if pattern.pattern_id == pattern_id:
            return pattern
    raise AssertionError(pattern_id)


def _bundle_candidate(anchor: tuple[int, int], pattern_id: str = "lin_e_len1") -> BundleCandidate:
    pattern = _pattern_by_id(pattern_id)
    occupied = frozenset((anchor[0] + o[0], anchor[1] + o[1]) for o in pattern.occupied_offsets)
    stub = (anchor[0] + pattern.output_stub_offset[0], anchor[1] + pattern.output_stub_offset[1])
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=True,
    )


def test_commit_replay_includes_extractor_overlay_cells() -> None:
    cand = _bundle_candidate((4, 4))
    commit = CommitResult(
        committed_ids=(cand.candidate_id,),
        reserved_route_cells=frozenset({*cand.occupied_cells, cand.output_stub, (7, 4)}),
        domain_version=1,
        conflicts=(),
    )
    payload, _diag = build_commit_replay_payload(
        commit,
        validation_passed=True,
        normal_count=1,
        commit_order=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
    )
    cells = payload.cell_overlay_json["cells"]
    assert any(c.get("cell_kind") == "shape_miner" for c in cells)
    assert any(c.get("cell_kind") == "shape_miner_extension" for c in cells)
    kinds = {c.get("kind") for c in cells}
    assert "route.committed_path" in kinds


def test_selection_overlay_uses_miner_cell_kind_not_belt_transport() -> None:
    cand = _bundle_candidate((3, 3))
    genome = PlacementGenome(commit_order=(cand.candidate_id,))
    payload = build_selection_replay_payload(genome, (cand,))
    for cell in payload.cell_overlay_json["cells"]:
        if cell.get("cell_kind") in ("shape_miner", "shape_miner_extension"):
            assert cell.get("transport_kind") == "none"
            assert "commit_state" not in cell
```

- [ ] **Step 2: Run tests — expect FAIL** (signature / missing rows)

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py::test_commit_replay_includes_extractor_overlay_cells -v --tb=short
```

- [ ] **Step 3: Update replay payload builders**

In `rttp_replay_diagnostics.py`:

1. Import projector helpers.
2. `build_candidates_replay_payload` — replace `overlay_cells_from_coords(..., kind="candidate.bundle", transport=...)` loop with `build_candidate_placement_overlay_rows(normal)`; keep rejected/macro overlays unchanged.
3. `build_selection_replay_payload` — use `build_selected_placement_overlay_rows`.
4. `build_commit_replay_payload` — add required kw-only `candidates_by_id: dict[str, BundleCandidate]`; call `build_confirmed_placement_overlay_rows`; **always** return `tuple[RttpReplayPayload, PlacementOverlayDiagnostics]` (no single-payload return).

**Breaking change ripple (MUST):** every caller uses:

```python
commit_payload, placement_diag = build_commit_replay_payload(...)
```

Never `payload = build_commit_replay_payload(...)` alone.

```python
def build_commit_replay_payload(
    commit_result: CommitResult,
    *,
    validation_passed: bool,
    normal_count: int,
    commit_order: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
) -> tuple[RttpReplayPayload, PlacementOverlayDiagnostics]:
    placement_rows, diag = build_confirmed_placement_overlay_rows(
        committed_ids=commit_result.committed_ids,
        candidates_by_id=candidates_by_id,
        reserved_route_cells=commit_result.reserved_route_cells,
    )
    cells = placement_rows
    ...
    return RttpReplayPayload(...), diag
```

5. Update `__all__` and typing exports.

- [ ] **Step 4: Fix all call sites (tuple unpack)**

Known call sites (grep `build_commit_replay_payload(` before merge):

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/optimization/pipeline.py` (~474, `_run_v01_rttp_pipeline`) | `commit_payload, placement_diag = ...`; merge diag into `metrics_json` |
| `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py` | `test_commit_payload_reports_validation_and_overlays_routes` — add `candidates_by_id`, tuple unpack, assert `kind=="route.committed_path"` still passes |
| `django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py` | return type + `__all__` |

**Do not change** `build_macro_commit_replay_payload` call site (~659) in this PR.

Update existing regression test:

```python
def test_commit_payload_reports_validation_and_overlays_routes() -> None:
    cand = _bundle_candidate((0, 0), pattern_id="lin_e_len0")
    commit = CommitResult(
        committed_ids=(cand.candidate_id,),
        reserved_route_cells=frozenset({(2, 0), (3, 0)}),
        domain_version=1,
        conflicts=(),
    )
    payload, diag = build_commit_replay_payload(
        commit,
        validation_passed=True,
        normal_count=1,
        commit_order=(cand.candidate_id,),
        candidates_by_id={cand.candidate_id: cand},
    )
    assert "validation_passed: True" in payload.description
    kinds = {c["kind"] for c in payload.cell_overlay_json.get("cells", [])}
    assert "route.committed_path" in kinds
    assert any(c.get("cell_kind") == "shape_miner" for c in payload.cell_overlay_json["cells"])
```

Pipeline excerpt:

```python
commit_payload, placement_diag = build_commit_replay_payload(
    commit_result,
    validation_passed=validation_passed,
    normal_count=len(generation.normal_candidates),
    commit_order=tuple(genome.commit_order),
    candidates_by_id=candidates_by_id,
)
metrics_json={
    ...
    "visible_miner_cell_count": placement_diag.visible_miner_cell_count,
    "visible_extension_cell_count": placement_diag.visible_extension_cell_count,
    "placement_route_overlap_warning_count": placement_diag.placement_route_overlap_warning_count,
    "placement_route_overlap_warning_coords": [
        [x, y] for x, y in placement_diag.placement_route_overlap_warning_coords
    ],
},
```

- [ ] **Step 5: Run replay diagnostics tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py -v --tb=short
```

Expected: PASS.

---

### Task 3: Import boundary guard test

**Files:**
- Create: `tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py`

- [ ] **Step 1: Add regression test**

```python
"""Placement overlay must not be imported by commit/probe/selection core."""

from __future__ import annotations

from pathlib import Path

_FORBIDDEN_FILES = (
    Path("django_apps/asteroid_lab/optimization/commit/incremental_commit.py"),
    Path("django_apps/asteroid_lab/optimization/commit/incremental_macro_commit.py"),
    Path("django_apps/asteroid_lab/optimization/routing/route_probe.py"),
    Path("django_apps/asteroid_lab/optimization/selection/greedy_regret.py"),
    Path("django_apps/asteroid_lab/optimization/selection/macro_greedy_regret.py"),
)

_ALLOWED_IMPORTER = Path(
    "django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py"
)


def test_core_modules_do_not_import_placement_overlay_projection() -> None:
    needle = "placement_overlay_projection"
    for path in _FORBIDDEN_FILES:
        source = path.read_text(encoding="utf-8")
        assert needle not in source, f"{path} must not import {needle}"


def test_replay_diagnostics_may_import_placement_overlay_projection() -> None:
    source = _ALLOWED_IMPORTER.read_text(encoding="utf-8")
    assert "placement_overlay_projection" in source
```

- [ ] **Step 2: Run test**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py -v --tb=short
```

Expected: PASS.

---

### Task 4: Full narrow gate + docs

**Files:** none (verification)

- [ ] **Step 1: Narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py -v --tb=short
```

Expected: PASS.

- [ ] **Step 2: Ruff + mypy (project gate slice)**

```powershell
python -m ruff check django_apps/asteroid_lab/optimization/materialization django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py django_apps/asteroid_lab/optimization/pipeline.py
python -m mypy django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py
```

Expected: PASS.

- [ ] **Step 3: Commit (when user requests git commit)**

```bash
git add django_apps/asteroid_lab/optimization/materialization \
  django_apps/asteroid_lab/optimization/rttp_replay_diagnostics.py \
  django_apps/asteroid_lab/optimization/pipeline.py \
  tests/unit/asteroid_lab/test_placement_overlay_projection.py \
  tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py \
  tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py \
  docs/superpowers/specs/2026-05-26-rttp-confirmed-placement-footprint-design.md
git commit -m "fix(asteroid-lab): project RTTP placement footprints into replay overlay"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| `placement_overlay_projection.py` three builders | Task 1 |
| Import boundary | Task 1 docstring + Task 3 |
| `transport_kind=none` on equipment | Task 1 tests |
| `commit_state` only on confirmed | Task 1 tests |
| Overlap metrics_json fixed keys | Task 1 `PlacementOverlayDiagnostics` + Task 2 pipeline |
| Visual-v0 Forward + rotation | Task 1 `_route_rows` / stub rows |
| Route `kind="route.committed_path"` preserved | Task 1 + Step 3b test |
| No incremental_commit change | Task 3 |
| Replay diagnostics wiring | Task 2 |
| Macro path deferred | Plan gate PR scope note |
| PR-2/3 out of scope | — |

**Placeholder scan:** None.

**Type consistency:** `build_commit_replay_payload` returns `(RttpReplayPayload, PlacementOverlayDiagnostics)` at every call site; no single-value assignment.

---

## Execution handoff

**Plan gate:** Approved for Subagent-Driven execution (2026-05-25 review corrections applied).

Plan saved to [`docs/superpowers/plans/2026-05-25-rttp-confirmed-placement-footprint.md`](2026-05-25-rttp-confirmed-placement-footprint.md).

**Execution order:**

```text
Task 0 baseline → Task 1 projector TDD → Task 2 replay wiring → Task 3 boundary guard → Task 4 narrow gate
```

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

Which approach do you want?
