# Track D+ PR-3 — Catalog-Native Candidate Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace production `generate_candidates` enumeration with catalog-slice placement specs so every normal `BundleCandidate` carries `catalog_placement_ref` and footprint-aligned `occupied_cells`; isolate `lin_*` / `build_pattern_library()` to pytest-only paths.

**Architecture:** `canonical_ids_for_transport_kind` filters variants; `catalog_output_attachment` derives rotated stub/dir; `build_catalog_placement_specs` emits frozen `CatalogPlacementSpec` tuples; `candidate_generator` iterates anchor × spec only (no synthetic patterns). Empty slice/specs → empty normal pool (pipeline candidate step already `passed=False` when `normal_count==0`).

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, StrEnum, pytest, ruff.

**Approved spec:** [`2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md`](../specs/2026-05-24-track-d-plus-pr3-catalog-native-generator-design.md)

**Prerequisite:** D+ PR-2 merged to `master`; `current_plan.md` lists PR-2 CLOSED.

**Recommended worktree:** `f:\Python_Projects\shapez2Factory\.worktrees\track-d-plus-pr3` on branch `feature/track-d-plus-pr3-catalog-native-generator`

---

## Out of scope (PR gate)

| Area | Reason |
|------|--------|
| `build_pattern_library()` in production `candidate_generator` | PR-3 removes |
| Dual-path / `catalog_slice is None` synthetic fallback | Forbidden |
| `synthetic_lin_pattern_count` pipeline metric | Arch gate only (spec §8) |
| Selection / fitness / macro / replay / commit reprobe | Forbidden |
| `validate_catalog_placements` logic changes | PR-2 owns |
| Connector mismatch fail-closed | Deferred |
| B-CS2 ops smoke | Separate track |

**Regression gates (final task):**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_catalog_output_attachment.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_generator_arch.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map and not synthetic_lin_patterns" -v
python -m ruff check django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/adapters/catalog_geometry_transform.py django_apps/asteroid_lab/adapters/catalog_output_attachment.py django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py
```

---

## File map

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/contracts/catalog_candidate.py` | **Create** `CatalogPlacementSpec`, `throughput_factor_for_footprint`, `catalog_pattern_id` |
| `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` | Add `canonical_ids_for_transport_kind` |
| `django_apps/asteroid_lab/adapters/catalog_geometry_transform.py` | Add public `rotate_coord`, `rotate_cardinal_direction`, `tile_direction_to_cardinal` |
| `django_apps/asteroid_lab/adapters/catalog_output_attachment.py` | **Create** stub/dir from connectors |
| `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py` | **Create** `build_catalog_placement_specs` |
| `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py` | Catalog-only enumeration + `bundle_pattern_from_spec` |
| `django_apps/asteroid_lab/optimization/candidates/pattern_library.py` | TEST-ONLY docstring |
| `tests/unit/asteroid_lab/conftest.py` | `catalog_slice_minimal`, `greenfield_with_catalog` |
| `tests/unit/asteroid_lab/test_catalog_transport_policy.py` | Extend T1 |
| `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py` | **Create** |
| `tests/unit/asteroid_lab/test_catalog_output_attachment.py` | **Create** T3 |
| `tests/unit/asteroid_lab/test_catalog_candidate_placements.py` | **Create** T2 |
| `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py` | **Create** T4 |
| `tests/unit/asteroid_lab/test_catalog_native_generator_arch.py` | **Create** T5 |
| `tests/unit/asteroid_lab/test_catalog_geometry_transform.py` | Add `synthetic_lin_patterns` marker |
| `tests/unit/asteroid_lab/test_rttp_candidate_generator.py` | Use `greenfield_with_catalog` |
| `pyproject.toml` | Register `synthetic_lin_patterns` marker |
| `documents/Algorithm/asteroid_lab_03_candidate_generator.md` | Catalog-native § |
| `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` | A7 on close |

---

### Task 0 — Preconditions (read-only)

**Rollback:** N/A

- [ ] **Step 1: Confirm PR-2 on `master`**

```powershell
git fetch origin
git log origin/master -1 --oneline
git merge-base --is-ancestor origin/feature/track-d-plus-pr2-mapped-fail-closed origin/master; if ($LASTEXITCODE -ne 0) { Write-Host "BLOCKED: merge PR-2 first" }
```

- [ ] **Step 2: Create worktree/branch**

```powershell
git worktree add .worktrees/track-d-plus-pr3 -b feature/track-d-plus-pr3-catalog-native-generator origin/master
cd .worktrees/track-d-plus-pr3
```

- [ ] **Step 3: Baseline narrow RTTP (expect PASS on master post PR-2)**

```powershell
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map" -v
```

---

### Task 1 — `CatalogPlacementSpec` contract

**Files:**
- Create: `django_apps/asteroid_lab/contracts/catalog_candidate.py`
- Test: `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py`

- [ ] **Step 1: Write failing contract tests**

```python
# tests/unit/asteroid_lab/test_catalog_candidate_contracts.py
from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_candidate import (
    CatalogPlacementSpec,
    catalog_pattern_id,
    throughput_factor_for_footprint,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection


def test_throughput_factor_matches_pattern_library_table() -> None:
    assert throughput_factor_for_footprint(1) == 4
    assert throughput_factor_for_footprint(2) == 8
    assert throughput_factor_for_footprint(3) == 12
    assert throughput_factor_for_footprint(4) == 16
    assert throughput_factor_for_footprint(99) == 16


def test_catalog_pattern_id_never_lin_prefix() -> None:
    pid = catalog_pattern_id("bv:miner", CardinalDirection.N)
    assert pid.startswith("cat_")
    assert "lin_" not in pid
    assert pid == "cat_bv_miner_N"


def test_catalog_placement_spec_frozen() -> None:
    spec = CatalogPlacementSpec(
        canonical_id="bv:1",
        rotation=CardinalDirection.E,
        pattern_id="cat_bv_1_E",
        occupied_offsets=frozenset({(0, 0)}),
        output_stub_offset=(1, 0),
        output_dir="E",
        throughput_factor=4,
    )
    assert spec.topology_kind == "catalog"
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v`  
Expected: `ModuleNotFoundError` or import error

- [ ] **Step 3: Implement contract module**

```python
# django_apps/asteroid_lab/contracts/catalog_candidate.py
from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord

_THROUGHPUT_BY_EXT: tuple[int, ...] = (4, 8, 12, 16)


def throughput_factor_for_footprint(cell_count: int) -> int:
    extension_count = min(3, max(0, cell_count - 1))
    return _THROUGHPUT_BY_EXT[extension_count]


def catalog_pattern_id(canonical_id: str, rotation: CardinalDirection) -> str:
    safe = canonical_id.replace(":", "_")
    return f"cat_{safe}_{rotation.value}"


@dataclass(frozen=True, slots=True)
class CatalogPlacementSpec:
    canonical_id: str
    rotation: CardinalDirection
    pattern_id: str
    occupied_offsets: frozenset[Coord]
    output_stub_offset: Coord
    output_dir: str
    throughput_factor: int
    topology_kind: str = "catalog"


__all__ = [
    "CatalogPlacementSpec",
    "catalog_pattern_id",
    "throughput_factor_for_footprint",
]
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_contracts.py -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/catalog_candidate.py tests/unit/asteroid_lab/test_catalog_candidate_contracts.py
git commit -m "feat(asteroid-lab): add CatalogPlacementSpec contract (D+ PR-3)"
```

---

### Task 2 — Transport filter helper

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_transport_policy.py`
- Test: `tests/unit/asteroid_lab/test_catalog_transport_policy.py`

- [ ] **Step 1: Write failing test**

```python
# append to tests/unit/asteroid_lab/test_catalog_transport_policy.py
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    canonical_ids_for_transport_kind,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantIdentity


def test_canonical_ids_for_transport_kind_filters_by_category() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (
            TransportRegistryEntry("space_belt", "belt", "bv:shape"),
            TransportRegistryEntry("fluid_pipe", "pipe", "bv:fluid"),
        ),
        (
            VariantIdentity("bv:shape", "shape"),
            VariantIdentity("bv:fluid", "fluid"),
        ),
        (),
    )
    shape_ids = canonical_ids_for_transport_kind(sl, TransportKind.SHAPE_BELT)
    assert shape_ids == frozenset({"bv:shape"})
    fluid_ids = canonical_ids_for_transport_kind(sl, TransportKind.FLUID_PIPE)
    assert fluid_ids == frozenset({"bv:fluid"})
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py::test_canonical_ids_for_transport_kind_filters_by_category -v`

- [ ] **Step 3: Implement helper**

```python
# django_apps/asteroid_lab/adapters/catalog_transport_policy.py
def canonical_ids_for_transport_kind(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> frozenset[str]:
    out: set[str] = set()
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        mapped = _TRANSPORT_CATEGORY_TO_KIND.get(category)
        if mapped is transport_kind:
            out.add(entry.building_variant_canonical_id)
    return frozenset(out)
```

Add to `__all__`: `"canonical_ids_for_transport_kind"`.

- [ ] **Step 4: Run full transport policy tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_transport_policy.py
git commit -m "feat(asteroid-lab): canonical_ids_for_transport_kind (D+ PR-3)"
```

---

### Task 3 — Geometry helpers + output attachment

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_geometry_transform.py`
- Create: `django_apps/asteroid_lab/adapters/catalog_output_attachment.py`
- Test: `tests/unit/asteroid_lab/test_catalog_output_attachment.py`

- [ ] **Step 1: Write failing output attachment tests**

```python
# tests/unit/asteroid_lab/test_catalog_output_attachment.py
from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import expected_footprint_coords
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)


def _variant_east_chain() -> VariantGeometryCatalog:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (
        BuildingConnectorSnapshot(
            0,
            "output",
            "East",
            "Regular",
            1,
            0,
            0,
        ),
    )
    return VariantGeometryCatalog("bv:test", "test", footprint, connectors)


def test_attachment_east_expected_stub_from_fixture() -> None:
    """Catalog fixture: output at (1,0), East → stub (2,0). No lin_* reference."""
    geom = _variant_east_chain()
    att = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att is not None
    assert att.output_stub_offset == (2, 0)
    assert att.output_dir == "E"
    occupied = expected_footprint_coords(
        geom.footprint_cells,
        anchor_coord=(0, 0),
        rotation=CardinalDirection.E,
    )
    assert att.output_stub_offset not in occupied


@pytest.mark.synthetic_lin_patterns
def test_attachment_n_rotation_differs_from_east_tile_direction_only() -> None:
    geom = _variant_east_chain()
    att_n = attachment_for_variant_rotation(geom, CardinalDirection.N)
    att_e = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att_n is not None and att_e is not None
    assert att_n.output_dir == "N"
    assert att_n.output_stub_offset != att_e.output_stub_offset


def test_attachment_north_tile_direction_uses_project_coord_convention() -> None:
    geom = VariantGeometryCatalog(
        "bv:north",
        "north",
        (BuildingFootprintCell(0, 0, 0),),
        (
            BuildingConnectorSnapshot(
                0,
                "output",
                "North",
                "Regular",
                0,
                0,
                0,
            ),
        ),
    )
    att = attachment_for_variant_rotation(geom, CardinalDirection.E)
    assert att is not None
    assert att.output_dir == "N"
    assert att.output_stub_offset == (0, -1)


def test_attachment_none_when_no_output_connector() -> None:
    geom = VariantGeometryCatalog("bv:x", "x", (BuildingFootprintCell(0, 0, 0),), ())
    assert attachment_for_variant_rotation(geom, CardinalDirection.E) is None
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_output_attachment.py -v`

- [ ] **Step 3: Extend `catalog_geometry_transform.py`**

Add after `_rotate_point` (export public wrappers; keep matrix private):

```python
# Matches pattern_library / _rotation_matrix convention: E=+x, N=-y, S=+y, W=-x.
_CARDINAL_UNIT: dict[CardinalDirection, Coord] = {
    CardinalDirection.E: (1, 0),
    CardinalDirection.N: (0, -1),
    CardinalDirection.S: (0, 1),
    CardinalDirection.W: (-1, 0),
}


def cardinal_unit_vector(direction: CardinalDirection) -> Coord:
    return _CARDINAL_UNIT[direction]


_TILE_TO_CARDINAL: dict[str, CardinalDirection] = {
    "east": CardinalDirection.E,
    "north": CardinalDirection.N,
    "south": CardinalDirection.S,
    "west": CardinalDirection.W,
}


def tile_direction_to_cardinal(tile_direction: str) -> CardinalDirection:
    key = tile_direction.strip().lower()
    try:
        return _TILE_TO_CARDINAL[key]
    except KeyError as exc:
        raise CatalogTransformError(f"unsupported tile_direction {tile_direction!r}") from exc


def rotate_cardinal_direction(
    direction: CardinalDirection,
    rotation: CardinalDirection,
) -> CardinalDirection:
    order = (
        CardinalDirection.E,
        CardinalDirection.N,
        CardinalDirection.S,
        CardinalDirection.W,
    )
    idx = order.index(direction)
    rot_idx = order.index(rotation)
    return order[(idx + rot_idx) % 4]


def rotate_coord(rotation: CardinalDirection, point: Coord) -> Coord:
    return _rotate_point(rotation, point)
```

Update `__all__` with: `cardinal_unit_vector`, `tile_direction_to_cardinal`, `rotate_cardinal_direction`, `rotate_coord` (do **not** export `_CARDINAL_UNIT`).

- [ ] **Step 4: Create `catalog_output_attachment.py`**

```python
# django_apps/asteroid_lab/adapters/catalog_output_attachment.py
from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    cardinal_unit_vector,
    expected_footprint_coords,
    rotate_cardinal_direction,
    rotate_coord,
    tile_direction_to_cardinal,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import VariantGeometryCatalog
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingConnectorSnapshot
from django_apps.asteroid_lab.optimization.coords import Coord


@dataclass(frozen=True, slots=True)
class CatalogOutputAttachment:
    output_stub_offset: Coord
    output_dir: str


def _primary_output_connector(
    geometry: VariantGeometryCatalog,
) -> BuildingConnectorSnapshot | None:
    candidates: list[BuildingConnectorSnapshot] = []
    for connector in geometry.connectors:
        role = connector.connector_role.strip().lower()
        if role in ("output", "item_output") or role.endswith("_output"):
            candidates.append(connector)
    if not candidates:
        return None
    return min(candidates, key=lambda c: c.order_index)


def attachment_for_variant_rotation(
    geometry: VariantGeometryCatalog,
    rotation: CardinalDirection,
) -> CatalogOutputAttachment | None:
    primary = _primary_output_connector(geometry)
    if primary is None:
        return None
    try:
        base_dir = tile_direction_to_cardinal(primary.tile_direction)
    except Exception:
        return None
    connector_local: Coord = (primary.position_x, primary.position_y)
    unit = cardinal_unit_vector(base_dir)
    base_stub = (connector_local[0] + unit[0], connector_local[1] + unit[1])
    stub_offset = rotate_coord(rotation, base_stub)
    rotated_dir = rotate_cardinal_direction(base_dir, rotation)
    try:
        occupied = expected_footprint_coords(
            geometry.footprint_cells,
            anchor_coord=(0, 0),
            rotation=rotation,
        )
    except Exception:
        return None
    if stub_offset in occupied:
        return None
    return CatalogOutputAttachment(
        output_stub_offset=stub_offset,
        output_dir=rotated_dir.value,
    )
```

Fix import: move `BuildingConnectorSnapshot` to top-level import (no inline import in function). Export `CatalogOutputAttachment`, `attachment_for_variant_rotation`.

- [ ] **Step 5: Register pytest marker in `pyproject.toml`**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "synthetic_lin_patterns: uses build_pattern_library lin_* (not production path)",
]
```

- [ ] **Step 6: Run output attachment tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_output_attachment.py -v`

- [ ] **Step 7: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_geometry_transform.py django_apps/asteroid_lab/adapters/catalog_output_attachment.py tests/unit/asteroid_lab/test_catalog_output_attachment.py pyproject.toml
git commit -m "feat(asteroid-lab): catalog output attachment + rotation helpers (D+ PR-3)"
```

---

### Task 4 — `build_catalog_placement_specs`

**Files:**
- Create: `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py`
- Test: `tests/unit/asteroid_lab/test_catalog_candidate_placements.py`

- [ ] **Step 1: Write failing placement spec tests**

```python
# tests/unit/asteroid_lab/test_catalog_candidate_placements.py
from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def _slice_with_output() -> BuildingCatalogSlice:
    footprint = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    connectors = (
        BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
    )
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        variants=(VariantIdentity("bv:1", "miner"),),
        variant_geometries=(
            VariantGeometryCatalog("bv:1", "miner", footprint, connectors),
        ),
    )


def test_build_specs_four_rotations_deterministic() -> None:
    specs = build_catalog_placement_specs(
        _slice_with_output(),
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert len(specs) == 4
    rotations = [s.rotation for s in specs]
    assert rotations == [
        CardinalDirection.E,
        CardinalDirection.N,
        CardinalDirection.S,
        CardinalDirection.W,
    ]
    assert all(s.pattern_id.startswith("cat_") for s in specs)
    assert all(s.throughput_factor == 8 for s in specs)


def test_build_specs_empty_when_transport_mismatch() -> None:
    sl = _slice_with_output()
    specs = build_catalog_placement_specs(sl, transport_kind=TransportKind.FLUID_PIPE)
    assert specs == ()
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_placements.py -v`

- [ ] **Step 3: Implement `catalog_candidate_placements.py`**

```python
# django_apps/asteroid_lab/adapters/catalog_candidate_placements.py
from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.adapters.catalog_output_attachment import (
    attachment_for_variant_rotation,
)
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    canonical_ids_for_transport_kind,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_candidate import (
    CatalogPlacementSpec,
    catalog_pattern_id,
    throughput_factor_for_footprint,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind

_CARDINAL_ORDER: tuple[CardinalDirection, ...] = (
    CardinalDirection.E,
    CardinalDirection.N,
    CardinalDirection.S,
    CardinalDirection.W,
)


def build_catalog_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[CatalogPlacementSpec, ...]:
    allowed = canonical_ids_for_transport_kind(catalog_slice, transport_kind)
    specs: list[CatalogPlacementSpec] = []
    for geometry in catalog_slice.variant_geometries:
        if geometry.canonical_id not in allowed:
            continue
        if not geometry.footprint_cells:
            continue
        cell_count = len(geometry.footprint_cells)
        throughput = throughput_factor_for_footprint(cell_count)
        for rotation in _CARDINAL_ORDER:
            try:
                occupied = expected_footprint_coords(
                    geometry.footprint_cells,
                    anchor_coord=(0, 0),
                    rotation=rotation,
                )
            except CatalogTransformError:
                continue
            attachment = attachment_for_variant_rotation(geometry, rotation)
            if attachment is None:
                continue
            pattern_id = catalog_pattern_id(geometry.canonical_id, rotation)
            specs.append(
                CatalogPlacementSpec(
                    canonical_id=geometry.canonical_id,
                    rotation=rotation,
                    pattern_id=pattern_id,
                    occupied_offsets=occupied,
                    output_stub_offset=attachment.output_stub_offset,
                    output_dir=attachment.output_dir,
                    throughput_factor=throughput,
                )
            )
    return tuple(
        sorted(specs, key=lambda s: (s.canonical_id, s.rotation.value, s.pattern_id))
    )


__all__ = ["build_catalog_placement_specs"]
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_placements.py -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_candidate_placements.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py
git commit -m "feat(asteroid-lab): build_catalog_placement_specs (D+ PR-3)"
```

---

### Task 5 — Conftest catalog fixtures

**Files:**
- Modify: `tests/unit/asteroid_lab/conftest.py`

- [ ] **Step 1: Add fixtures (no new test file)**

```python
# append imports + fixtures to tests/unit/asteroid_lab/conftest.py
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    TransportRegistryEntry,
)


@pytest.fixture
def catalog_slice_minimal() -> BuildingCatalogSlice:
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    connectors = (
        BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),
    )
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        variants=(VariantIdentity("bv:1", "miner"),),
        variant_geometries=(
            VariantGeometryCatalog("bv:1", "miner", footprint, connectors),
        ),
    )


@pytest.fixture
def greenfield_with_catalog(
    greenfield_optimization_input: OptimizationInput,
    catalog_slice_minimal: BuildingCatalogSlice,
) -> OptimizationInput:
    return replace(
        greenfield_optimization_input,
        catalog_slice=catalog_slice_minimal,
    )
```

Add `from dataclasses import replace` if missing.

- [ ] **Step 2: Smoke import fixtures**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_placements.py -v` (still PASS)

- [ ] **Step 3: Commit**

```bash
git add tests/unit/asteroid_lab/conftest.py
git commit -m "test(asteroid-lab): catalog_slice_minimal fixtures (D+ PR-3)"
```

---

### Task 6 — Catalog-native `candidate_generator`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/candidate_generator.py`
- Test: `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py`

- [ ] **Step 1: Write failing generator tests**

```python
# tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py
from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    expected_footprint_coords,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import (
    RttpSkeletonBuilder,
)


def test_generate_candidates_all_normal_have_catalog_ref(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    assert result.normal_candidates
    for cand in result.normal_candidates:
        assert cand.catalog_placement_ref is not None
        assert cand.pattern.pattern_id.startswith("cat_")
        assert "lin_" not in cand.pattern.pattern_id


def test_generate_candidates_slice_none_returns_empty_normal(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    assert inp.catalog_slice is None
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton)
    assert result.normal_candidates == ()
    assert result.rejected_candidates == ()


def test_normal_occupied_matches_catalog_footprint(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    result = generate_candidates(inp, skeleton, policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM)
    sl = inp.catalog_slice
    assert sl is not None
    for cand in result.normal_candidates:
        ref = cand.catalog_placement_ref
        assert ref is not None
        geom = next(
            g for g in sl.variant_geometries if g.canonical_id == ref.canonical_id
        )
        expected = expected_footprint_coords(
            geom.footprint_cells,
            anchor_coord=ref.anchor_coord,
            rotation=ref.rotation,
        )
        assert cand.occupied_cells == expected
```

- [ ] **Step 2: Run test — expect FAIL** (generator still uses `build_pattern_library`)

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v`

- [ ] **Step 3: Rewrite `candidate_generator.py`**

Replace `build_pattern_library` import with:

```python
from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.contracts.catalog_candidate import CatalogPlacementSpec
from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementRef
```

Add helpers:

```python
def _bundle_pattern_from_spec(spec: CatalogPlacementSpec) -> BundlePattern:
    sorted_cells = sorted(spec.occupied_offsets)
    extractor = sorted_cells[0]
    extensions = tuple(c for c in sorted_cells if c != extractor)
    return BundlePattern(
        pattern_id=spec.pattern_id,
        extension_count=min(3, max(0, len(sorted_cells) - 1)),
        occupied_offsets=spec.occupied_offsets,
        extractor_offset=extractor,
        extension_offsets=extensions,
        output_dir=spec.output_dir,
        output_stub_offset=spec.output_stub_offset,
        throughput_factor=spec.throughput_factor,
        topology_kind=spec.topology_kind,
    )


def _project_spec(anchor: Coord, spec: CatalogPlacementSpec) -> tuple[frozenset[Coord], Coord]:
    occupied = frozenset(_translate_offset(anchor, o) for o in spec.occupied_offsets)
    output_stub = _translate_offset(anchor, spec.output_stub_offset)
    return occupied, output_stub
```

In `generate_candidates`:

```python
if inp.catalog_slice is None:
    return CandidateGenerationResult(normal_candidates=(), rejected_candidates=())

specs = build_catalog_placement_specs(inp.catalog_slice, transport_kind=inp.transport_kind)
# loop: for anchor in anchors: for spec in specs:
#   pattern = _bundle_pattern_from_spec(spec)
#   ref = CatalogPlacementRef(spec.canonical_id, anchor, spec.rotation)
#   BundleCandidate(..., catalog_placement_ref=ref)
```

Update `_validate_geometry` to accept `occupied_offset_count: int` instead of `pattern` for overlap check, or pass `spec.occupied_offsets`.

Update `_make_candidate_id` to accept `pattern_id: str`.

- [ ] **Step 4: Run native generator tests — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v`

- [ ] **Step 4b: Gate — generator must not import pattern_library**

Run: `python -m pytest tests/unit/asteroid_lab/test_catalog_native_generator_arch.py -v`  
If `candidate_generator.py` still imports `build_pattern_library` or `pattern_library`, **stop and fix before Task 7**.

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/candidates/candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py
git commit -m "feat(asteroid-lab): catalog-native candidate generator (D+ PR-3)"
```

---

### Task 7 — `lin_*` isolation + RTTP test migration

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/candidates/pattern_library.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_geometry_transform.py`
- Modify: `tests/unit/asteroid_lab/test_rttp_candidate_generator.py`
- Create: `tests/unit/asteroid_lab/test_catalog_native_generator_arch.py`

- [ ] **Step 1: Add TEST-ONLY docstring to `pattern_library.py`**

```python
"""SYNTHETIC TEST-ONLY linear bundle patterns (lin_*).

Production RTTP uses ``adapters.catalog_candidate_placements.build_catalog_placement_specs``.
Do not call ``build_pattern_library()`` from ``candidate_generator`` or pipeline code.
"""
```

- [ ] **Step 2: Mark synthetic geometry test**

```python
# tests/unit/asteroid_lab/test_catalog_geometry_transform.py
import pytest

@pytest.mark.synthetic_lin_patterns
def test_catalog_geometry_transform_matches_pattern_library_east_rotation() -> None:
    ...
```

- [ ] **Step 3: Migrate `test_rttp_candidate_generator.py` to catalog fixture**

```python
def test_candidate_generator_does_not_commit(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    ...

def test_interior_and_rim_unreachable_goes_to_rejected(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = replace(greenfield_with_catalog, route_goals=())
    ...

def test_reachable_candidate_in_normal_pool(
    greenfield_with_catalog: OptimizationInput,
) -> None:
    inp = greenfield_with_catalog
    ...
```

- [ ] **Step 4: Write arch test**

```python
# tests/unit/asteroid_lab/test_catalog_native_generator_arch.py
from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_GENERATOR = (
    _REPO
    / "django_apps"
    / "asteroid_lab"
    / "optimization"
    / "candidates"
    / "candidate_generator.py"
)


def test_candidate_generator_does_not_reference_build_pattern_library() -> None:
    tree = ast.parse(_GENERATOR.read_text(encoding="utf-8-sig"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.ImportFrom) and node.module:
            if "pattern_library" in node.module:
                raise AssertionError(f"imports pattern_library: {node.module}")
    assert "build_pattern_library" not in names
```

- [ ] **Step 5: Run RTTP tests excluding synthetic marker**

Run: `python -m pytest tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_generator_arch.py -v`  
Run: `python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map and not synthetic_lin_patterns" -v`

- [ ] **Step 6: Commit**

```bash
git add django_apps/asteroid_lab/optimization/candidates/pattern_library.py tests/unit/asteroid_lab/test_catalog_geometry_transform.py tests/unit/asteroid_lab/test_rttp_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_generator_arch.py
git commit -m "test(asteroid-lab): isolate lin_* patterns; arch gate generator (D+ PR-3)"
```

---

### Task 8 — Documentation

**Files:**
- Modify: `documents/Algorithm/asteroid_lab_03_candidate_generator.md`
- Modify: `docs/superpowers/2026-05-24-asteroid-lab-catalog-rttp-roadmap.md` (on PR close)

- [ ] **Step 1: Add catalog-native section to `asteroid_lab_03_candidate_generator.md`**

English paragraph:

```markdown
## Catalog-native generation (Track D+ PR-3)

Production ``generate_candidates`` enumerates ``CatalogPlacementSpec`` values from
``OptimizationInput.catalog_slice`` via ``build_catalog_placement_specs``. Every normal
``BundleCandidate`` sets ``catalog_placement_ref`` at generation time.
``build_pattern_library()`` / ``lin_*`` patterns are **test-only** (``synthetic_lin_patterns`` marker).
```

- [ ] **Step 2: Commit docs**

```bash
git add documents/Algorithm/asteroid_lab_03_candidate_generator.md
git commit -m "docs(asteroid-lab): catalog-native candidate generator (D+ PR-3)"
```

---

### Task 9 — Final regression + Ops E5

**Files:** none (verification only)

- [ ] **Step 1: PR-3 narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_catalog_output_attachment.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py tests/unit/asteroid_lab/test_catalog_native_generator_arch.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v
python -m pytest tests/unit/asteroid_lab/ -k "rttp and not macro_real_map and not synthetic_lin_patterns" -v
python -m ruff check django_apps/asteroid_lab/contracts/catalog_candidate.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/adapters/catalog_geometry_transform.py django_apps/asteroid_lab/adapters/catalog_output_attachment.py django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/optimization/candidates/candidate_generator.py
```

Expected: all PASS

- [ ] **Step 2: Ops smoke E5 (manual, real DB slug)**

```powershell
python manage.py run_solver --slug copy-import-495e552c
```

Verify from persisted `solver_run` / summary:

- exit 0
- step `rttp.catalog_placement_validation` present
- `unmapped_candidate_count == 0`
- `checked_candidate_count > 0`
- candidate pool step `normal_count > 0`, `passed == true`
- `validation_passed == true`, `issue_codes == []`

Record `solver_run_id` in PR description.

- [ ] **Step 3: Update roadmap A7 + `current_plan.md` CLOSED (separate docs commit when PR merges)**

---

## Plan self-review

| Spec section | Task |
|--------------|------|
| SC-1 no `build_pattern_library` in generator | Task 6, 7 arch |
| SC-2 all normal have ref | Task 6 tests |
| SC-3 footprint match | Task 6 tests |
| SC-4 empty pool / passed=False | Task 6 slice None; pipeline existing |
| SC-5 Ops E5 | Task 9 |
| SC-6 arch import ban | Task 9 + existing arch test |
| Throughput 4/8/12/16 | Task 1 |
| Rotated stub/dir | Task 3 |
| `cardinal_unit_vector` public (no `_UNIT_VECTOR` import) | Task 3 |
| `canonical_ids_for_transport_kind` public | Task 2 |
| No `synthetic_lin_pattern_count` metric | Out of scope |
| lin_* test isolation | Task 7 |

**Placeholder scan:** none.

---

## Plan corrections (2026-05-24, pre-execution)

| # | Correction | Applied in |
|---|------------|------------|
| 1 | No `_UNIT_VECTOR` private import; use public `cardinal_unit_vector` | Task 3 |
| 2 | `test_catalog_output_attachment` uses fixture hard-coded `(2,0)` / `"E"`, not `build_pattern_library` | Task 3 |
| 3 | Task 6 imports: `RttpSkeletonBuilder` from `skeleton_builder`; `RttpSkeletonConfig` from `input_contracts` | Task 6 |
| 4 | Task 6 footprint test: lookup `sl.variant_geometries` by `canonical_id`, no `_variant_geometry` | Task 6 |
| 5 | `cardinal_unit_vector`: N=(0,-1), S=(0,1) per RTTP rotation convention; North connector test | Task 3 |

---

## Execution handoff

**Mode:** Subagent-Driven (`subagent-driven-development`). One subagent per Task (0–9); RED → GREEN → commit per task; targeted pytest after each task.

**Execution rules:**

1. If PR-2 is **not** on `master`, **BLOCK** at Task 0 (do not implement).
2. Each task: failing test → run fail → implement → run pass → commit.
3. After Task 6: `candidate_generator.py` must not import `build_pattern_library` or `pattern_library` (arch test + manual grep).
4. **Forbidden edits:** macro, selection, fitness, replay, commit reprobe, PR-2 validation logic.
5. Task 9: narrow gate + Ops E5 + plan self-review.

**Worktree:** `.worktrees/track-d-plus-pr3` on `feature/track-d-plus-pr3-catalog-native-generator` from `origin/master` (post PR-2).
