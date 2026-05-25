# Asteroid Game-Data Transport Projection — Phase A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire RTTP / Lab surfaces through **game_data-backed asteroid projection modules** so catalog-native paths never use `*InternalVariant*` factory belts; route `tile_type` identity is owned by `asteroid_transport_projection.resolve_route_tile` (not overlay hardcoding).

**Architecture:** Add read-only projection layer under `django_apps/asteroid_lab/catalog/` (`projection_source`, `asteroid_transport_projection`, `asteroid_equipment_projection`, `asteroid_sprite_projection`). Consumers (`catalog_candidate_placements`, `placement_overlay_projection`, `catalog_placement_audit`, solver summary) call projection DTOs only. Missing dump rows use `TEMPORARY_COMPAT` with audit exposure; equipment uses explicit layout allowlist + DB validation.

**Tech Stack:** Python 3.12+, Django 5.x, pytest, ruff, mypy (`django_apps config src`)

**Spec:** [`docs/superpowers/specs/2026-05-26-asteroid-game-data-transport-projection-design.md`](../specs/2026-05-26-asteroid-game-data-transport-projection-design.md)

**Branch (recommended):** `feat/asteroid-game-data-transport-projection-phase-a`

**Work classification:** contract change · implementation change

### Locked premises (from spec decision record)

| # | Premise |
|---|---------|
| Q1 | `ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST` + DB validation; `CANON_MANUAL` for island gaps |
| Q2 | Phase B = game_data export/import only (out of this plan) |
| Q3 | `resolve_route_tile` owns PR-1b turn synthesis; overlay is consumer |

### Plan corrections (2026-05-26 — Release Controller)

| # | Fix | Rule |
|---|-----|------|
| 1 | `ProjectedTransportTile.footprint_cells` | **Required** per spec; Phase A compat tiles use 1×1 stub `(0,0)` |
| 2 | `ProjectedEquipmentSpec.throughput_factor` | **`int`** only (`4` / `8` / `12` / `16` via `throughput_factor_for_footprint`) |
| 3 | `temporary_compat_count` | `temporary_compat_count` is **Phase A instrumentation only**. It must be **reset at solver/catalog step entry** before projection calls. **Long-term authoritative metric** = emitted projection DTOs: count rows where `source_kind == ProjectionSourceKind.TEMPORARY_COMPAT` (`count_temporary_compat`) |

### Execution mode

**Subagent-Driven** — Task 0 baseline → Task 1 DTO → review → Task 2 transport → … → Task 9 narrow gate.

### PR-1 / PR-1b merge note

If local WIP exists on `placement_overlay_projection.py` (route turn tests), **rebase onto this branch** before Task 6. Task 6 **moves** `_route_segment_tile_and_rotation` into transport projection — do not duplicate logic.

**Must NOT modify:** `incremental_commit.py`, route probe, selection/evolution cores, `game_data` importers (Phase B).

---

## File map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `django_apps/asteroid_lab/catalog/projection_source.py` | `ProjectionSourceKind`, `ProjectedTransportTile`, `ProjectedEquipmentSpec` |
| Create | `django_apps/asteroid_lab/catalog/asteroid_transport_projection.py` | Internal* exclusion, compat Space* tiles, `resolve_route_tile` |
| Create | `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py` | Allowlist + `list_equipment_placement_specs` |
| Create | `django_apps/asteroid_lab/catalog/asteroid_sprite_projection.py` | `resolve_sprite_ref` (DB + compat) |
| Modify | `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py` | Equipment specs from equipment projection |
| Modify | `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` | Placement allowlist via transport projection; document non-placement use |
| Modify | `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py` | Delegate route `tile_type` to `resolve_route_tile` |
| Modify | `django_apps/asteroid_lab/adapters/catalog_placement_audit.py` | `projection_source_kind` on rows / metrics |
| Modify | `django_apps/asteroid_lab/optimization/rttp_solver_summary.py` | `temporary_compat_count` in catalog step |
| Create | `tests/unit/asteroid_lab/test_projection_source.py` | DTO / enum smoke |
| Create | `tests/unit/asteroid_lab/test_asteroid_transport_projection.py` | Transport + route tile tests |
| Create | `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py` | Allowlist + Internal* exclusion |
| Create | `tests/unit/asteroid_lab/test_asteroid_sprite_projection.py` | Resolver + compat flag |
| Create | `tests/unit/asteroid_lab/test_projection_import_boundary.py` | Projection not imported by commit/probe |
| Modify | `tests/unit/asteroid_lab/test_catalog_candidate_placements.py` | No `InternalVariant` in pattern_id |
| Modify | `tests/unit/asteroid_lab/test_placement_overlay_projection.py` | `tile_type` via projection; route turn tests |
| Modify | `tests/unit/asteroid_lab/test_catalog_transport_policy.py` | Placement IDs exclude internal belt |
| Modify | `tests/unit/asteroid_lab/test_catalog_placement_audit.py` | `projection_source_kind` present |

---

### Task 0: Branch and baseline

**Files:** none

- [ ] **Step 1: Create branch**

```powershell
Set-Location F:\Python_Projects\shapez2Factory
git checkout master
git pull
git checkout -b feat/asteroid-game-data-transport-projection-phase-a
```

- [ ] **Step 2: Baseline narrow gate (pre-edit)**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_catalog_placement_audit.py -v --tb=short
```

Expected: PASS (records current behavior; may include PR-1b route tests if already on branch).

---

### Task 1: `projection_source` DTOs

**Files:**
- Create: `django_apps/asteroid_lab/catalog/projection_source.py`
- Create: `tests/unit/asteroid_lab/test_projection_source.py`

- [ ] **Step 1: Write failing test**

Create `tests/unit/asteroid_lab/test_projection_source.py`:

```python
from django_apps.asteroid_lab.catalog.projection_source import (
    COMPAT_TRANSPORT_STUB_FOOTPRINT,
    ProjectionSourceKind,
    ProjectedTransportTile,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_projection_source_kind_values_are_stable_strings() -> None:
    assert ProjectionSourceKind.GAME_DATA_CANON.value == "game_data_canon"
    assert ProjectionSourceKind.TEMPORARY_COMPAT.value == "temporary_compat"
    assert ProjectionSourceKind.CANON_MANUAL.value == "canon_manual"


def test_projected_transport_tile_is_frozen() -> None:
    row = ProjectedTransportTile(
        layout_t="SpaceBelt_Forward",
        transport_kind=TransportKind.SHAPE_BELT,
        canonical_id=None,
        footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT,
        source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
        source_detail="compat:route_forward",
    )
    assert row.layout_t == "SpaceBelt_Forward"
    assert len(row.footprint_cells) == 1
```

- [ ] **Step 2: Run test — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_projection_source.py -v --tb=short
```

- [ ] **Step 3: Implement `projection_source.py`**

```python
"""Shared projection DTOs — adapter view over game_data, not SoT."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.game_data_snapshot import BuildingFootprintCell
from django_apps.asteroid_lab.contracts.catalog_placement import CardinalDirection
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


class ProjectionSourceKind(StrEnum):
    GAME_DATA_CANON = "game_data_canon"
    TEMPORARY_COMPAT = "temporary_compat"
    CANON_MANUAL = "canon_manual"


COMPAT_TRANSPORT_STUB_FOOTPRINT: Final[tuple[BuildingFootprintCell, ...]] = (
    BuildingFootprintCell(x=0, y=0, order_index=0),
)


@dataclass(frozen=True, slots=True)
class ProjectedTransportTile:
    layout_t: str
    transport_kind: TransportKind
    canonical_id: str | None
    footprint_cells: tuple[BuildingFootprintCell, ...]
    source_kind: ProjectionSourceKind
    source_detail: str


@dataclass(frozen=True, slots=True)
class ProjectedEquipmentSpec:
    layout_t: str
    canonical_id: str
    pattern_id: str
    occupied_offsets: tuple[Coord, ...]
    output_stub_offset: Coord
    output_dir: CardinalDirection
    throughput_factor: int
    source_kind: ProjectionSourceKind
    source_detail: str


def count_temporary_compat(projected: Sequence[ProjectedTransportTile | ProjectedEquipmentSpec]) -> int:
    """Canonical compat metric — prefer over module counter."""
    return sum(1 for p in projected if p.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT)
```

(Add `ProjectedSpriteRef` in Task 5 if needed.)

- [ ] **Step 4: Run test — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_projection_source.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/catalog/projection_source.py tests/unit/asteroid_lab/test_projection_source.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/catalog/projection_source.py tests/unit/asteroid_lab/test_projection_source.py
git commit -m "feat(asteroid): add projection source DTOs for game_data view"
```

---

### Task 2: `asteroid_transport_projection` (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/catalog/asteroid_transport_projection.py`
- Create: `tests/unit/asteroid_lab/test_asteroid_transport_projection.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/asteroid_lab/test_asteroid_transport_projection.py`:

```python
from django_apps.asteroid_lab.catalog.asteroid_transport_projection import (
    is_factory_internal_variant,
    placement_transport_canonical_ids,
    resolve_route_tile,
)
from django_apps.asteroid_lab.catalog.projection_source import ProjectionSourceKind
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    TransportRegistryEntry,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant


def test_is_factory_internal_variant_suffix() -> None:
    assert is_factory_internal_variant("BeltDefaultForwardInternalVariant") is True
    assert is_factory_internal_variant("Layout_ShapeMiner") is False


def test_placement_transport_canonical_ids_excludes_internal_belt() -> None:
    sl = _slice_with_variant(
        canonical_id="bv:internal",
        internal_name="BeltDefaultForwardInternalVariant",
    )
    sl = BuildingCatalogSlice(
        slice_version=sl.slice_version,
        transport_registry=(
            TransportRegistryEntry("ForwardBelt", "belt", "bv:internal"),
        ),
        variants=sl.variants,
        variant_geometries=sl.variant_geometries,
    )
    allowed = placement_transport_canonical_ids(sl, TransportKind.SHAPE_BELT)
    assert "bv:internal" not in allowed


def test_resolve_route_tile_straight_forward_compat() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=0,
    )
    assert tile.layout_t == "SpaceBelt_Forward"
    assert tile.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT


def test_resolve_route_tile_left_turn_compat() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=1,
    )
    assert tile.layout_t == "SpaceBelt_LeftTurn"
    assert tile.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT


def test_resolve_route_tile_includes_stub_footprint() -> None:
    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=0,
    )
    assert len(tile.footprint_cells) == 1


def test_count_temporary_compat_from_dto_list() -> None:
    from django_apps.asteroid_lab.catalog.projection_source import count_temporary_compat

    tile = resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=1,
    )
    assert count_temporary_compat((tile,)) == 1
```

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_transport_projection.py -v --tb=short
```

- [ ] **Step 3: Implement transport projection**

`django_apps/asteroid_lab/catalog/asteroid_transport_projection.py` must include:

```python
def is_factory_internal_variant(internal_name: str) -> bool:
    return internal_name.endswith("InternalVariant")


def placement_transport_canonical_ids(
    catalog_slice: BuildingCatalogSlice,
    transport_kind: TransportKind,
) -> frozenset[str]:
    """DB-backed placement allowlist; excludes InternalVariant rows."""


def resolve_route_tile(
    *,
    transport_kind: TransportKind,
    incoming_dir: int | None,
    outgoing_dir: int | None,
) -> ProjectedTransportTile:
    """PR-1b turn/forward synthesis — moved from placement_overlay_projection."""
```

Move logic from `placement_overlay_projection._route_segment_tile_and_rotation` (incoming/outgoing dir ints 0..3). Always set `source_kind=TEMPORARY_COMPAT`, `footprint_cells=COMPAT_TRANSPORT_STUB_FOOTPRINT`, and `source_detail` like `compat:route_left_turn` until Phase B adds DB rows.

**Compat metric (canonical):** `count_temporary_compat(sequence)` in `projection_source.py`. Task 7 pipeline/audit uses **emitted projection DTO lists**, not a leaking global.

Optional dev-only `temporary_compat_count` counter may exist for tests but must call `reset()` at `run_rttp_pipeline` / `solver_runtime_entry` entry; do not use as sole production metric.

- [ ] **Step 4: Run — expect PASS**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_transport_projection.py -v --tb=short
python -m ruff check django_apps/asteroid_lab/catalog/asteroid_transport_projection.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/catalog/asteroid_transport_projection.py tests/unit/asteroid_lab/test_asteroid_transport_projection.py
git commit -m "feat(asteroid): transport projection with route tile resolve"
```

---

### Task 3: `asteroid_equipment_projection` (TDD)

**Files:**
- Create: `django_apps/asteroid_lab/catalog/asteroid_equipment_projection.py`
- Create: `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py`

- [ ] **Step 1: Write failing tests**

```python
from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST,
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.catalog.projection_source import ProjectionSourceKind
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_allowlist_contains_layout_miners() -> None:
    assert "Layout_ShapeMiner" in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST
    assert "Layout_FluidMiner" in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST


def test_specs_never_use_internal_variant_canonical_id(
    catalog_slice_with_shape_miner,
) -> None:
    specs = list_equipment_placement_specs(
        catalog_slice_with_shape_miner,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert specs
    for spec in specs:
        assert "InternalVariant" not in spec.canonical_id
        assert "InternalVariant" not in spec.pattern_id
```

Add fixture `catalog_slice_with_shape_miner` in the test file: variant whose `internal_name` is `Layout_ShapeMiner` (or use `island_extractor_defaults` row + `CANON_MANUAL` when DB row missing — assert `source_kind`).

- [ ] **Step 2: Run — expect FAIL**

```powershell
python -m pytest tests/unit/asteroid_lab/test_asteroid_equipment_projection.py -v --tb=short
```

- [ ] **Step 3: Implement equipment projection**

```python
ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST: Final[frozenset[str]] = frozenset({
    "Layout_ShapeMiner",
    "Layout_FluidMiner",
})


def list_equipment_placement_specs(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind,
) -> tuple[ProjectedEquipmentSpec, ...]:
    ...
```

Rules:
- Include variants where `internal_name in ASTEROID_EQUIPMENT_LAYOUT_ALLOWLIST` and geometry validates (reuse `expected_footprint_coords` / `attachment_for_variant_rotation` from adapters).
- If slice lacks variant but allowlist name is known → emit spec from `island_extractor_defaults` with `CANON_MANUAL`.
- Never emit `BeltDefault*InternalVariant`.

Map `ProjectedEquipmentSpec` → `CatalogPlacementSpec` in Task 4.

- [ ] **Step 4: Run — expect PASS + ruff**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(asteroid): equipment projection with explicit layout allowlist"
```

---

### Task 4: Wire `catalog_candidate_placements`

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_candidate_placements.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_candidate_placements.py`

- [ ] **Step 1: Write failing test**

```python
def test_build_catalog_placement_specs_excludes_internal_belt_variant(
    catalog_slice_forward_belt_internal,
) -> None:
    specs = build_catalog_placement_specs(
        catalog_slice_forward_belt_internal,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert specs
    assert all("InternalVariant" not in s.canonical_id for s in specs)
    assert all("InternalVariant" not in s.pattern_id for s in specs)
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Replace spec builder body**

```python
from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    list_equipment_placement_specs,
)

def build_catalog_placement_specs(...) -> tuple[CatalogPlacementSpec, ...]:
    projected = list_equipment_placement_specs(catalog_slice, transport_kind=transport_kind)
    # map ProjectedEquipmentSpec → CatalogPlacementSpec (sorted stable)
```

Remove dependency on `canonical_ids_for_transport_kind` for placement enumeration.

- [ ] **Step 4: Run catalog + candidate tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git commit -m "fix(asteroid): catalog placement specs from equipment projection only"
```

---

### Task 5: `asteroid_sprite_projection` (minimal Phase A)

**Files:**
- Create: `django_apps/asteroid_lab/catalog/asteroid_sprite_projection.py`
- Create: `tests/unit/asteroid_lab/test_asteroid_sprite_projection.py`

- [ ] **Step 1: Failing test — DB path + compat fallback**

```python
def test_resolve_sprite_ref_layout_miner_db_first(db_with_layout_shape_miner_sprite) -> None:
    ref = resolve_sprite_ref(layout_t="Layout_ShapeMiner", import_batch_id=1)
    assert ref.source_kind is ProjectionSourceKind.GAME_DATA_CANON
    assert ref.sprite_path


def test_resolve_sprite_ref_unknown_uses_compat_with_audit() -> None:
    ref = resolve_sprite_ref(layout_t="SpaceBelt_Forward", import_batch_id=1)
    assert ref.source_kind is ProjectionSourceKind.TEMPORARY_COMPAT
```

Use existing `game_data` test fixtures (`tests/unit/game_data/fixtures.py`) where possible; skip DB test if no seeded sprite — use `@pytest.mark.django_db` + minimal `GameContentAsset` row.

- [ ] **Step 2–4: Implement resolver**

Query `GameContentAsset` / `AssetMetaReference` by `layout_t` / identifier value; fallback to `admin_lab_sprites.LAB_SPRITE_CELL_KIND_FALLBACK` mapping with `TEMPORARY_COMPAT` only.

**Phase A does not require Lab JS changes** — expose function for future API; optional: add thin wrapper in `admin_lab_sprites.lab_sprite_resolve` calling projection when `tile_type` set.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(asteroid): sprite projection with DB-first resolver"
```

---

### Task 6: Refactor `placement_overlay_projection` (Q3)

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py`
- Modify: `tests/unit/asteroid_lab/test_placement_overlay_projection.py`

- [ ] **Step 1: Update route tests to assert projection ownership**

Ensure `test_route_l_shape_corner_uses_turn_tile_pr1b` (if present) still passes after refactor.

Add test:

```python
from django_apps.asteroid_lab.catalog.asteroid_transport_projection import resolve_route_tile

def test_route_rows_delegates_tile_type_to_transport_projection(monkeypatch) -> None:
    calls: list[tuple[int | None, int | None]] = []

    def spy(**kwargs):
        calls.append((kwargs["incoming_dir"], kwargs["outgoing_dir"]))
        return resolve_route_tile(**kwargs)

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.materialization.placement_overlay_projection.resolve_route_tile",
        spy,
    )
    rows = _route_rows(frozenset({(1, 0), (1, 1), (2, 1)}), transport_kind=TransportKind.SHAPE_BELT)
    assert any(r["tile_type"] == "SpaceBelt_LeftTurn" for r in rows)
    assert calls
```

- [ ] **Step 2: Run — expect FAIL if not wired**

- [ ] **Step 3: Refactor `_route_rows`**

- Delete `_route_segment_tile_and_rotation` and `_transport_sprite_prefix` tile synthesis.
- Import `resolve_route_tile` from `asteroid_transport_projection`.
- For each segment, set overlay row `tile_type=projected.layout_t`, optional metadata `projection_source_kind=projected.source_kind.value` on wire dict if spec requires (align with audit Task 7).

Equipment `layout_t` for miners may call equipment projection in follow-up sub-step or keep existing `_equipment_kinds` until equipment projection exposes `resolve_equipment_tile(anchor, field_kind)` — **minimum:** route cells only in Task 6.

- [ ] **Step 4: Run overlay + import boundary tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py -v --tb=short
```

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor(asteroid): overlay route tiles via transport projection"
```

---

### Task 7: Audit + solver summary metrics

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_placement_audit.py`
- Modify: `django_apps/asteroid_lab/optimization/rttp_solver_summary.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_placement_audit.py`

- [ ] **Step 1: Failing test for `projection_source_kind` in audit metrics**

```python
def test_audit_metrics_include_temporary_compat_count() -> None:
    metrics = catalog_placement_audit_metrics(...)
    assert "temporary_compat_count" in metrics
```

- [ ] **Step 2: Implement**

- When audit compares canonical vs wire, attach `projection_source_kind` from projected rows.
- **Prefer DTO-based aggregation** when projected rows are available: `count_temporary_compat(...)` over emitted transport/equipment (and route tiles when collected for audit).
- **Module counter** (if any) is instrumentation only for route-tile calls that do not yet persist DTO lists; **reset before each run** at `run_rttp_pipeline` / `solver_runtime_entry` / catalog step entry; never the sole `metrics_json` source.

- [ ] **Step 3: Run tests**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_placement_audit.py tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(asteroid): expose projection compat counts in RTTP audit"
```

---

### Task 8: `catalog_transport_policy` + import boundary

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_transport_policy.py`
- Modify: `tests/unit/asteroid_lab/test_catalog_transport_policy.py`
- Create: `tests/unit/asteroid_lab/test_projection_import_boundary.py`

- [ ] **Step 1: Deprecate placement use of `canonical_ids_for_transport_kind`**

Add module docstring: placement must use `placement_transport_canonical_ids`; keep `canonical_ids_for_transport_kind` for wire-key resolution tests only or delegate to transport projection.

Update test:

```python
def test_canonical_ids_for_transport_kind_still_resolves_registry_for_wire_keys() -> None:
    ...

def test_placement_transport_canonical_ids_excludes_internal() -> None:
    from django_apps.asteroid_lab.catalog.asteroid_transport_projection import (
        placement_transport_canonical_ids,
    )
    ...
```

- [ ] **Step 2: Import boundary test**

```python
FORBIDDEN_IMPORTERS = [
    "django_apps/asteroid_lab/optimization/incremental_commit.py",
    "django_apps/asteroid_lab/optimization/route_probe.py",
]

def test_projection_not_imported_by_solver_commit_internals() -> None:
    ...
```

Mirror `test_placement_overlay_import_boundary.py` pattern with explicit `Path` grep.

- [ ] **Step 3: Run + commit**

```bash
git commit -m "test(asteroid): transport policy and projection import boundaries"
```

---

### Task 9: Narrow gate + documentation sync

**Files:**
- Modify: `docs/superpowers/specs/2026-05-26-asteroid-game-data-transport-projection-design.md` (status → Phase A implemented when done)

- [x] **Step 1: Narrow pytest gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_projection_source.py tests/unit/asteroid_lab/test_asteroid_transport_projection.py tests/unit/asteroid_lab/test_asteroid_equipment_projection.py tests/unit/asteroid_lab/test_asteroid_sprite_projection.py tests/unit/asteroid_lab/test_projection_import_boundary.py tests/unit/asteroid_lab/test_catalog_candidate_placements.py tests/unit/asteroid_lab/test_placement_overlay_projection.py tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_placement_audit.py -v --tb=short
```

- [x] **Step 2: ruff + mypy (narrow)**

```powershell
python -m ruff check django_apps/asteroid_lab/catalog django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py
python -m mypy django_apps/asteroid_lab/catalog django_apps/asteroid_lab/adapters/catalog_candidate_placements.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/optimization/materialization/placement_overlay_projection.py
```

- [x] **Step 3: Update spec status line**

Set spec header: `Phase A implemented YYYY-MM-DD` when all green.

- [ ] **Step 4: Optional manual Lab smoke**

Fluid field map → Run Solver → commit frame: `Layout_FluidMiner` + `SpaceBelt_*`; solver summary shows `temporary_compat_count` ≥ 0 until Phase B.

**PR / full gate:** defer to PR checklist (`scripts/test_full.ps1`, full pytest) per AGENTS.md — not required to complete each task commit.

---

## Plan self-review (spec coverage)

| Spec requirement | Task |
|------------------|------|
| projection 3 modules + `projection_source` | 1–5 |
| Equipment explicit allowlist + DB validation | 3–4 |
| Internal* excluded from placement | 2, 4 |
| `resolve_route_tile` owns PR-1b | 2, 6 |
| `TEMPORARY_COMPAT` + audit count | 2, 7 |
| Sprite DB-first + compat | 5 |
| Consumer wiring (candidates, overlay, audit) | 4, 6, 7 |
| Import boundary | 8 |
| §4 tests | 1–8 |

**Out of scope (Phase B+):** game_data export changes, Lab JS resolver-only, removing all compat tables.

---

## Execution handoff

Plan saved. Choose execution mode when ready to implement:

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — same session, `executing-plans` checkpoints

Which approach?
