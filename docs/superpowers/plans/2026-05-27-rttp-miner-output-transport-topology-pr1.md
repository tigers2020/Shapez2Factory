# RTTP Miner Output Transport Topology — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop catalog-native RTTP from placing extension/miner sprites on the R (output-axis) transport cell and align throughput/occupied semantics with `GeneTemplate` (Phase 1: zero extensions, explicit `fixed_output_transport_offset`).

**Architecture:** Add `miner_placement_topology` normalization (footprint evidence ≠ occupied). Thread `fixed_output_transport_offset` through `CatalogPlacementSpec` → `BundlePattern` → overlay rows. Reject candidates that violate INV-R. Do not edit `incremental_commit.py`; rely on existing `final_validation` disjoint rule + new tests.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Spec:** [`docs/superpowers/specs/2026-05-27-rttp-miner-output-transport-topology-design.md`](../specs/2026-05-27-rttp-miner-output-transport-topology-design.md)

**Branch:** `feat/rttp-miner-output-transport-topology-pr1`

**Work classification:** contract change · implementation change

**Must NOT modify:** `incremental_commit.py`, route probe core, selection/evolution, `game_data` importers, `exhaustive_generator.py` production imports.

**Gate review (2026-05-27):** Spec approved. Plan execution = **Subagent-Driven** after micro-fixes below (committed in this revision). **Do not commit** until user requests.

**Implementation status (2026-05-27):** Phase 1 WIP landed on branch `feat/rttp-miner-output-transport-topology-pr1` — narrow gate 43 passed; `incremental_commit.py` untouched.

### Pre-execution micro-fixes (applied in this plan)

| # | Fix |
|---|-----|
| 1 | Task 2: output-axis assert uses component-wise tuple math, not `tuple + tuple` concat |
| 2 | Task 2: remove unused `rotate_coord` import from test module |
| 3 | Task 2/5: Phase 1 requires `extractor_offset == (0, 0)` in normalizer; `_validate_geometry` uses `anchor` + `_translate_offset` only |
| 4 | Task 6: FOT row uses transport priority/cell_kind; must not render as miner/extension |
| 5 | Task 7: test-local `_bundle_candidate` factory (not bare `BundleCandidate(...)`) |

### Subagent-Driven execution map

| Subagent | Tasks | Gate after |
|----------|-------|------------|
| Contract/DTO | Task 1–2 | `test_miner_placement_topology` + ruff green |
| Candidate pipeline | Task 3–5 | `test_catalog_native_candidate_generator` green |
| Overlay/validation | Task 6–7 | overlay + `test_final_validation_route_disjoint` green |
| Gate/docs | Task 8 | narrow pytest + mypy scope |

---

## File map

| Action | Path |
|--------|------|
| Create | `django_apps/asteroid_lab/catalog/miner_placement_topology.py` |
| Modify | `django_apps/asteroid_lab/contracts/catalog_candidate.py` |
| Modify | `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py` |
| Modify | `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/bundle_pattern.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py` |
| Modify | `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py` |
| Modify | `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py` |
| Create | `tests/unit/asteroid_lab/test_miner_placement_topology.py` |
| Modify | `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py` |
| Modify | `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py` |
| Modify | `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py` |
| Modify | `tests/unit/asteroid_lab/test_placement_overlay_projection.py` |
| Create | `tests/unit/asteroid_lab/test_final_validation_route_disjoint.py` |
| Modify | `docs/superpowers/specs/2026-05-26-rttp-confirmed-placement-footprint-design.md` (semantic row) |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/rttp-miner-output-transport-topology-pr1
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_equipment_projection.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v --tb=short
```

Expected: PASS (records behavior before topology fix; some tests will change in later tasks).

---

### Task 1: Throughput helper + reject enums

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/catalog_candidate.py`
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py`:

```python
from django_apps.asteroid_lab.contracts.catalog_candidate import (
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    CandidateRejectReason,
)


def test_throughput_factor_for_extension_count_matches_pattern_library() -> None:
    assert throughput_factor_for_extension_count(0) == 4
    assert throughput_factor_for_extension_count(1) == 8
    assert throughput_factor_for_extension_count(2) == 12
    assert throughput_factor_for_extension_count(3) == 16
    assert throughput_factor_for_extension_count(99) == 16


def test_candidate_reject_reason_transport_topology_codes_exist() -> None:
    assert (
        CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED.value
        == "fixed_output_transport_in_occupied"
    )
    assert (
        CandidateRejectReason.ROUTE_PROBE_START_IN_OCCUPIED.value
        == "route_probe_start_in_occupied"
    )
    assert (
        CandidateRejectReason.EXTENSION_ON_OUTPUT_AXIS.value
        == "extension_on_output_axis"
    )
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_contracts.py::test_throughput_factor_for_extension_count_matches_pattern_library tests/unit/asteroid_lab/test_catalog_candidate_contracts.py::test_candidate_reject_reason_transport_topology_codes_exist -v --tb=short
```

- [ ] **Step 3: Implement**

In `catalog_candidate.py` add:

```python
def throughput_factor_for_extension_count(extension_count: int) -> int:
    clamped = min(3, max(0, extension_count))
    return _THROUGHPUT_BY_EXT[clamped]
```

Keep `throughput_factor_for_footprint` with docstring: **DEPRECATED for equipment — audit only.**

In `candidate_dtos.py` extend `CandidateRejectReason`:

```python
class CandidateRejectReason(StrEnum):
    NOT_REACHABLE = "not_reachable"
    GEOMETRY_INVALID = "geometry_invalid"
    OVERLAP = "overlap"
    FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED = "fixed_output_transport_in_occupied"
    ROUTE_PROBE_START_IN_OCCUPIED = "route_probe_start_in_occupied"
    EXTENSION_ON_OUTPUT_AXIS = "extension_on_output_axis"
```

Export new helper in `__all__`.

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v --tb=short
```

- [ ] **Step 5: Commit** (when user requests commit)

```bash
git add django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/optimization/candidates/candidate_dtos.py tests/unit/asteroid_lab/test_catalog_candidate_contracts.py
git commit -m "feat(asteroid_lab): add extension-count throughput and topology reject enums"
```

---

### Task 2: `miner_placement_topology` normalizer

**Files:**
- Create: `django_apps/asteroid_lab/catalog/miner_placement_topology.py`
- Create: `tests/unit/asteroid_lab/test_miner_placement_topology.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_miner_placement_topology.py`:

```python
from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    cardinal_unit_vector,
)
from django_apps.asteroid_lab.catalog.miner_placement_topology import (
    normalize_miner_placement_topology,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    VariantGeometryCatalog,
)


def _geometry_two_cell_east_output() -> VariantGeometryCatalog:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (
        BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
    )
    return VariantGeometryCatalog(
        canonical_id="bv:test_miner",
        internal_name="Layout_ShapeMiner",
        footprint_cells=footprint,
        connectors=connectors,
    )


def test_manual_two_cell_east_topology_phase1() -> None:
    topo = normalize_miner_placement_topology(
        _geometry_two_cell_east_output(),
        rotation=CardinalDirection.E,
    )
    assert topo is not None
    assert topo.extractor_offset == (0, 0)
    assert topo.fixed_output_transport_offset == (1, 0)
    assert topo.output_stub_offset == (2, 0)
    assert topo.extension_offsets == ()
    assert topo.occupied_offsets == frozenset({(0, 0)})
    assert topo.footprint_evidence == frozenset({(0, 0), (1, 0)})
    assert topo.throughput_factor == 4
    assert topo.output_dir == "E"


@pytest.mark.parametrize(
    ("rotation", "expected_fot", "expected_stub"),
    [
        (CardinalDirection.E, (1, 0), (2, 0)),
        (CardinalDirection.N, (0, -1), (0, -2)),
        (CardinalDirection.S, (0, 1), (0, 2)),
        (CardinalDirection.W, (-1, 0), (-2, 0)),
    ],
)
def test_rotation_matrix_invariants_nesw(
    rotation: CardinalDirection,
    expected_fot: tuple[int, int],
    expected_stub: tuple[int, int],
) -> None:
    topo = normalize_miner_placement_topology(
        _geometry_two_cell_east_output(),
        rotation=rotation,
    )
    assert topo is not None
    unit = cardinal_unit_vector(
        CardinalDirection(topo.output_dir)
        if topo.output_dir in ("N", "E", "S", "W")
        else CardinalDirection.E
    )
    assert topo.fixed_output_transport_offset == expected_fot
    assert topo.output_stub_offset == expected_stub
    assert topo.fixed_output_transport_offset not in topo.occupied_offsets
    assert topo.output_stub_offset not in topo.occupied_offsets
    output_axis = (
        topo.extractor_offset[0] + unit[0],
        topo.extractor_offset[1] + unit[1],
    )
    assert output_axis not in topo.extension_offsets
    assert topo.output_stub_offset == (
        topo.fixed_output_transport_offset[0] + unit[0],
        topo.fixed_output_transport_offset[1] + unit[1],
    )


def test_ambiguous_extractor_candidates_returns_none() -> None:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(2, 0, 1),
    )
    connectors = (
        BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
    )
    geometry = VariantGeometryCatalog(
        canonical_id="bv:ambiguous",
        internal_name="Layout_ShapeMiner",
        footprint_cells=footprint,
        connectors=connectors,
    )
    assert (
        normalize_miner_placement_topology(geometry, rotation=CardinalDirection.E)
        is None
    )
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_placement_topology.py -v --tb=short
```

- [ ] **Step 3: Implement `miner_placement_topology.py`**

Core logic (implement fully in file):

```python
"""Normalize catalog miner footprints to GeneTemplate-aligned topology (Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    cardinal_unit_vector,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.contracts.catalog_candidate import (
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import VariantGeometryCatalog
from django_apps.asteroid_lab.optimization.coords import Coord


@dataclass(frozen=True, slots=True)
class MinerPlacementTopology:
    canonical_id: str
    rotation: CardinalDirection
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    fixed_output_transport_offset: Coord
    output_stub_offset: Coord
    output_dir: str
    throughput_factor: int
    footprint_evidence: frozenset[Coord]

    @property
    def occupied_offsets(self) -> frozenset[Coord]:
        return frozenset({self.extractor_offset}) | frozenset(self.extension_offsets)


def _resolve_extractor_offset(
    footprint_evidence: frozenset[Coord],
    fixed_output_transport_offset: Coord,
    *,
    explicit_catalog_anchor: Coord | None,
) -> Coord | None:
    candidates = footprint_evidence - {fixed_output_transport_offset}
    if len(candidates) == 1:
        return next(iter(candidates))
    if explicit_catalog_anchor is not None and explicit_catalog_anchor in candidates:
        return explicit_catalog_anchor
    return None


def normalize_miner_placement_topology(
    geometry: VariantGeometryCatalog,
    rotation: CardinalDirection,
    *,
    explicit_catalog_anchor: Coord | None = None,
) -> MinerPlacementTopology | None:
    attachment = attachment_for_variant_rotation(geometry, rotation)
    if attachment is None:
        return None
    try:
        footprint_evidence = expected_footprint_coords(
            geometry.footprint_cells,
            anchor_coord=(0, 0),
            rotation=rotation,
        )
    except CatalogTransformError:
        return None
    output_dir = CardinalDirection(attachment.output_dir)
    unit = cardinal_unit_vector(output_dir)
    output_stub_offset = attachment.output_stub_offset
    fixed_output_transport_offset = (
        output_stub_offset[0] - unit[0],
        output_stub_offset[1] - unit[1],
    )
    extractor_offset = _resolve_extractor_offset(
        footprint_evidence,
        fixed_output_transport_offset,
        explicit_catalog_anchor=explicit_catalog_anchor,
    )
    if extractor_offset is None:
        return None
    if extractor_offset != (0, 0):
        return None
    extension_offsets: tuple[Coord, ...] = ()
    occupied = frozenset({extractor_offset}) | frozenset(extension_offsets)
    if fixed_output_transport_offset in occupied:
        return None
    if output_stub_offset in occupied:
        return None
    output_axis = (extractor_offset[0] + unit[0], extractor_offset[1] + unit[1])
    if output_axis in extension_offsets:
        return None
    if output_stub_offset != (
        fixed_output_transport_offset[0] + unit[0],
        fixed_output_transport_offset[1] + unit[1],
    ):
        return None
    throughput_factor = throughput_factor_for_extension_count(len(extension_offsets))
    return MinerPlacementTopology(
        canonical_id=geometry.canonical_id,
        rotation=rotation,
        extractor_offset=extractor_offset,
        extension_offsets=extension_offsets,
        fixed_output_transport_offset=fixed_output_transport_offset,
        output_stub_offset=output_stub_offset,
        output_dir=output_dir.value,
        throughput_factor=throughput_factor,
        footprint_evidence=footprint_evidence,
    )
```

- [ ] **Step 4: Run tests — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_placement_topology.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/catalog/miner_placement_topology.py tests/unit/asteroid_lab/test_miner_placement_topology.py
```

- [ ] **Step 5: Commit** (when user requests)

---

### Task 3: `BundlePattern.fixed_output_transport_offset`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/bundle_pattern.py`
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py`

- [ ] **Step 1: Write failing test**

Add to `test_catalog_native_candidate_generator.py`:

```python
def test_normal_candidate_has_empty_extensions_and_fot_not_occupied(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    assert result.normal_candidates
    cand = result.normal_candidates[0]
    anchor = cand.anchor_coord
    fot = (
        anchor[0] + cand.pattern.fixed_output_transport_offset[0],
        anchor[1] + cand.pattern.fixed_output_transport_offset[1],
    )
    assert cand.pattern.extension_offsets == ()
    assert fot not in cand.occupied_cells
    assert cand.throughput_factor == 4
```

- [ ] **Step 2: Run — expect FAIL** (AttributeError or assertion)

- [ ] **Step 3: Add field to `BundlePattern`**

```python
fixed_output_transport_offset: Coord
```

Update `_bundle_pattern_from_spec` in `candidate_generator.py`:

```python
def _bundle_pattern_from_spec(spec: CatalogPlacementSpec) -> BundlePattern:
    return BundlePattern(
        pattern_id=spec.pattern_id,
        extension_count=len(spec.extension_offsets),
        occupied_offsets=spec.occupied_offsets,
        extractor_offset=spec.extractor_offset,
        extension_offsets=spec.extension_offsets,
        output_dir=spec.output_dir,
        output_stub_offset=spec.output_stub_offset,
        fixed_output_transport_offset=spec.fixed_output_transport_offset,
        throughput_factor=spec.throughput_factor,
        topology_kind=spec.topology_kind,
    )
```

Update `pattern_library._canonical_linear_east` for **`extension_count == 0`** (production-aligned test baseline):

```python
# len0 only — matches INV-R
extractor = (0, 0)
extension_offsets: tuple[Coord, ...] = ()
occupied = frozenset({extractor})
fixed_output_transport_offset = (1, 0)
output_stub_offset = (2, 0)
```

For `len >= 1`, synthetic `lin_*` patterns remain **TEST-ONLY** (`@pytest.mark.synthetic_lin_patterns`); add `fixed_output_transport_offset` field for compile compatibility but do not use them in catalog-native generator tests.

Fix every other `BundlePattern(...)` call site to pass `fixed_output_transport_offset`.

- [ ] **Step 4: Run targeted tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v --tb=short
```

- [ ] **Step 5: Commit** (when user requests)

---

### Task 4: Extend `CatalogPlacementSpec` + placements adapter

**Files:**
- Modify: `django_apps/asteroid_lab/catalog/projection_source.py` (`ProjectedEquipmentSpec`: add `extractor_offset`, `extension_offsets`, `fixed_output_transport_offset`; keep `occupied_offsets` derived)
- Modify: `django_apps/asteroid_lab/contracts/catalog_candidate.py`
- Modify: `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py`
- Modify: `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py`
- Modify: `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py`

- [ ] **Step 1: Extend `CatalogPlacementSpec`**

```python
@dataclass(frozen=True, slots=True)
class CatalogPlacementSpec:
    canonical_id: str
    rotation: CardinalDirection
    pattern_id: str
    extractor_offset: Coord
    extension_offsets: tuple[Coord, ...]
    fixed_output_transport_offset: Coord
    output_stub_offset: Coord
    occupied_offsets: frozenset[Coord]
    output_dir: str
    throughput_factor: int
    topology_kind: str = "catalog"
```

Add property or factory `from_topology(topo: MinerPlacementTopology, pattern_id: str) -> CatalogPlacementSpec`.

- [ ] **Step 2: Refactor `asteroid_equipment_projection._specs_from_geometry`**

Replace footprint-length throughput and raw occupied with:

```python
topo = normalize_miner_placement_topology(geometry, rotation)
if topo is None:
    continue
# emit ProjectedEquipmentSpec using topo fields; throughput from topo.throughput_factor
```

Update `_MANUAL_FOOTPRINT` path to use same normalizer (2-cell manual geometry fixture).

- [ ] **Step 3: Update `build_catalog_placement_specs`**

Map `ProjectedEquipmentSpec` → `CatalogPlacementSpec` including all offset fields; `occupied_offsets` from topology property.

- [ ] **Step 4: Update `test_asteroid_equipment_projection.py`**

```python
def test_two_cell_shape_miner_spec_occupies_extractor_only(
    catalog_slice_with_shape_miner,
) -> None:
    specs = list_equipment_placement_specs(
        catalog_slice_with_shape_miner,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    east = [s for s in specs if s.rotation is CardinalDirection.E][0]
    assert (1, 0) not in east.occupied_offsets
    assert east.throughput_factor == 4
```

- [ ] **Step 5: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_equipment_projection.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py -v --tb=short
```

- [ ] **Step 6: Commit** (when user requests)

---

### Task 5: Generator geometry gates

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py`

- [ ] **Step 1: Replace `_validate_geometry` (anchor-absolute; Phase 1 local origin)**

**Phase 1 rule:** every emitted `CatalogPlacementSpec` has `extractor_offset == (0, 0)` (enforced in `normalize_miner_placement_topology`). Generator translates with `anchor` only:

```python
def _validate_geometry(
    inp: OptimizationInput,
    spec: CatalogPlacementSpec,
    anchor: Coord,
    occupied: frozenset[Coord],
    output_stub: Coord,
) -> CandidateRejectReason | None:
    if spec.extractor_offset != (0, 0):
        return CandidateRejectReason.GEOMETRY_INVALID
    if len(occupied) != len(spec.occupied_offsets):
        return CandidateRejectReason.OVERLAP
    if not occupied.issubset(inp.mineable_cells):
        return CandidateRejectReason.GEOMETRY_INVALID

    fot_abs = _translate_offset(anchor, spec.fixed_output_transport_offset)
    stub_abs = _translate_offset(anchor, spec.output_stub_offset)
    if fot_abs in occupied:
        return CandidateRejectReason.FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED
    if stub_abs in occupied:
        return CandidateRejectReason.ROUTE_PROBE_START_IN_OCCUPIED
    if output_stub != stub_abs:
        return CandidateRejectReason.GEOMETRY_INVALID

    unit = cardinal_unit_vector(CardinalDirection(spec.output_dir))
    axis_local = (
        spec.extractor_offset[0] + unit[0],
        spec.extractor_offset[1] + unit[1],
    )
    if axis_local in spec.extension_offsets:
        return CandidateRejectReason.EXTENSION_ON_OUTPUT_AXIS
    return None
```

Update the `generate_candidates` loop to pass `anchor` into `_validate_geometry`.

Remove `_bundle_pattern_from_spec` sorted_cells heuristic (done in Task 3).

- [ ] **Step 2: Run generator tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v --tb=short
```

- [ ] **Step 3: Commit** (when user requests)

---

### Task 6: Overlay `fixed_output_transport` semantic

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py`
- Modify: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`
- Modify: `docs/superpowers/specs/2026-05-26-rttp-confirmed-placement-footprint-design.md`

**Overlay priority contract:** `fixed_output_transport` is a **transport** row, not equipment. Use `cell_kind` / `transport_kind` from `_transport_channel` (same as output stub/belt) and existing `_ROW_PRIORITY` for `space_belt` / `space_pipe` (20). It must **not** render as miner/extension and must **not** override extractor/extension rows at the same coord (equipment priority 30 wins only on true equipment cells; FOT must not use extension semantic).

- [ ] **Step 1: Write failing overlay tests**

```python
@pytest.mark.parametrize("output_dir", ["E", "N", "W"])
def test_overlay_fixed_output_transport_not_extension(output_dir: str) -> None:
    # build minimal BundleCandidate with pattern offsets for output_dir
    # call build_candidate_placement_overlay_rows
    # assert semantic at fot coord contains fixed_output_transport
    # assert no extension semantic at fot coord
```

Use `cardinal_unit_vector` + rotate canonical E pattern for N/W.

- [ ] **Step 2: Update `_rows_for_candidate`**

After extractor row, before extension loop:

```python
rows.append(
    _base_row(
        at(pattern.fixed_output_transport_offset),
        kind=stub_semantic.replace("output_stub", "fixed_output_transport"),
        cell_kind=belt_ck,
        tile_type=belt_tt,
        transport_kind=belt_tk,
        overlay_semantic_kind=stub_semantic.replace(
            "output_stub", "fixed_output_transport"
        ),
        rotation=_OUTPUT_DIR_TO_ROTATION.get(candidate.output_dir, 0),
        ...
    )
)
```

Prefer explicit parameters `fot_semantic: str` on `_rows_for_candidate` instead of string replace — update all call sites:

- `placement.candidate_fixed_output_transport`
- `placement.selected_fixed_output_transport`
- `placement.confirmed_fixed_output_transport`

- [ ] **Step 3: Add semantic row to footprint spec table** (one table row).

- [ ] **Step 4: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_projection.py -v --tb=short
```

- [ ] **Step 5: Commit** (when user requests)

---

### Task 7: Validation regression (commit path B)

**Files:**
- Create: `tests/unit/asteroid_lab/test_final_validation_route_disjoint.py`

- [ ] **Step 1: Write test** (test-local factory — do not use incomplete `BundleCandidate(...)` literals)

Create `tests/unit/asteroid_lab/test_final_validation_route_disjoint.py`:

```python
from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput, TransportKind
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


def _minimal_pattern_e() -> BundlePattern:
    return BundlePattern(
        pattern_id="test_min_e_len0",
        extension_count=0,
        occupied_offsets=frozenset({(0, 0)}),
        extractor_offset=(0, 0),
        extension_offsets=(),
        output_dir="E",
        fixed_output_transport_offset=(1, 0),
        output_stub_offset=(2, 0),
        throughput_factor=4,
        topology_kind="test",
    )


def _bundle_candidate(
    candidate_id: str,
    anchor: Coord,
    *,
    occupied: frozenset[Coord],
    output_stub: Coord,
) -> BundleCandidate:
    pattern = _minimal_pattern_e()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=pattern.throughput_factor,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=None,
    )


def test_validate_final_layout_rejects_equipment_on_reserved_route(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    extractor = _bundle_candidate(
        "ext",
        (0, 0),
        occupied=frozenset({(0, 0)}),
        output_stub=(2, 0),
    )
    other = _bundle_candidate(
        "oth",
        (5, 5),
        occupied=frozenset({(5, 5)}),
        output_stub=(7, 5),
    )
    reserved = frozenset({(0, 0), (1, 0)})
    assert (
        validate_final_layout(
            (extractor.candidate_id, other.candidate_id),
            reserved,
            {
                extractor.candidate_id: extractor,
                other.candidate_id: other,
            },
            inp,
        )
        is False
    )
```

- [ ] **Step 2: Run — expect PASS** (behavior already exists)

```powershell
python -m pytest tests/unit/asteroid_lab/test_final_validation_route_disjoint.py -v --tb=short
```

- [ ] **Step 3: Commit** (when user requests)

---

### Task 8: Narrow gate + doc footnotes

**Files:**
- Modify: `docs/superpowers/specs/2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md` (§5.3 footnote)
- Modify: `docs/superpowers/specs/2026-05-26-asteroid-game-data-transport-projection-design.md` (equipment evidence line)

- [ ] **Step 1: Full narrow pytest**

```powershell
python -m pytest tests/unit/asteroid_lab/test_miner_placement_topology.py tests/unit/asteroid_lab/test_asteroid_equipment_projection.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_catalog_candidate_contracts.py tests/unit/asteroid_lab/test_final_validation_route_disjoint.py -v --tb=short
```

- [ ] **Step 2: Ruff + mypy**

```powershell
python -m ruff check django_apps/asteroid_lab/catalog/miner_placement_topology.py django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/optimization/candidates/
python -m mypy django_apps/asteroid_lab/catalog/miner_placement_topology.py django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py
```

- [ ] **Step 3: Update `documents/ai/current_plan.md`** — add active line for this PR (not CLOSED until merge).

- [ ] **Step 4: Commit** (when user requests)

```bash
git commit -m "docs: miner output transport topology spec and phase 1 plan"
```

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| INV-R-01..08 | Task 2, 5 |
| Footprint evidence ≠ occupied | Task 2, 4 |
| `BundlePattern.fixed_output_transport_offset` | Task 3 |
| Fail-closed extractor (no min xy) | Task 2 |
| Phase 1 `extractor_offset == (0,0)` | Task 2, 5 |
| Gate micro-fixes 1–5 | Plan header |
| Overlay FOT semantic | Task 6 |
| equipment ∩ reserved_route = ∅ | Task 7 |
| N/E/S/W tests | Task 2, 6 |
| No incremental_commit edit | Enforced in header |
| Phase 2 not in scope | Separate follow-up spec |

**Placeholder scan:** None.

---

## Phase 2 follow-up (out of plan)

Separate branch/spec after Phase 1 merges:

- `catalog/extension_topology_contract.py` (production-safe N/W/S tree)
- Allowlist `Layout_*MinerExtension`
- Do **not** import `exhaustive_generator` from optimization production code

---

## Execution handoff

**Plan saved to** `docs/superpowers/plans/2026-05-27-rttp-miner-output-transport-topology-pr1.md`.

**Spec saved to** `docs/superpowers/specs/2026-05-27-rttp-miner-output-transport-topology-design.md`.

**Approved execution mode:** **Subagent-Driven (1)** — use subagent map above; **executing-plans** / **subagent-driven-development** at implementation time.

**Status:** Plan-only complete (Gate Review micro-fixes merged). **No code changes, no commits** until user requests implementation start.
