# Track D — Catalog Footprint & Connector Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `BuildingCatalogSlice` to v2 with per-variant footprint and connector geometry, bump `catalog_slice_hash`/provenance version, and add output-only RTTP footprint catalog metrics — without changing placement, macro, selection, or validation behavior.

**Architecture:** `catalog_slice_from_snapshot` copies sorted geometry from `BuildingSnapshot` into frozen `VariantGeometryCatalog` rows. `catalog_footprint_policy` summarizes counts for metrics only. `solver_runtime_entry` / pipeline attaches metrics after `OptimizationInput` is built. `optimization/*` continues to forbid direct geometry snapshot imports (INV-D-04).

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, pytest, ruff.

**Approved spec:** [`2026-05-24-track-d-catalog-footprint-connector-design.md`](../specs/2026-05-24-track-d-catalog-footprint-connector-design.md)

**Predecessors (CLOSED on `master`):** B2-T1 `1c4baecd`, B2-T3 PR #61, B2-T2 PR #62

**Recommended worktree:** `f:\Python_Projects\shapez2Factory\.worktrees\track-d-catalog-footprint` on branch `feature/track-d-catalog-footprint`

---

## Out of scope (PR gate)

| Area | Reason |
|------|--------|
| `optimization/macros/**`, macro E2E | Macro track PAUSE |
| `optimization/selection/**`, fitness, regret | Forbidden |
| Validation relax / new bypass | Forbidden |
| Route-domain / probe / `RouteDomainSnapshotBuilder` | Separate track |
| Replay frames → algorithm input | Forbidden |
| Connector-based routing or placement scoring | Future Track D+ |

**Regression gates (stay green):**

```powershell
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_building_catalog_slice.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py -v
python -m pytest tests/unit/asteroid_lab/ -k rttp --ignore=tests/unit/asteroid_lab/test_rttp_macro_real_map_e2e.py
powershell -File scripts/test_reconstruction_narrow.ps1
python -m ruff check django_apps/asteroid_lab/contracts django_apps/asteroid_lab/adapters/catalog_footprint_policy.py django_apps/asteroid_lab/services/solver_runtime_entry.py
```

---

## File map

| File | Change |
|------|--------|
| `django_apps/asteroid_lab/contracts/building_catalog_slice.py` | v2 types, extract geometry |
| `django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py` | hash payload geometry |
| `django_apps/asteroid_lab/adapters/catalog_footprint_policy.py` | **Create** summarize + lookup |
| `django_apps/asteroid_lab/optimization/pipeline.py` | metrics step (or entry helper) |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | wire metrics if not in pipeline |
| `tests/unit/asteroid_lab/test_building_catalog_slice.py` | v2 extract + hash tests |
| `tests/unit/asteroid_lab/test_catalog_footprint_policy.py` | **Create** |
| `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py` | v2 version expectations |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | metrics present on RTTP run |
| `docs/domain/asteroid_game_data_snapshot.md` | Track D paragraph |
| `documents/ai/current_plan.md` | ACTIVE Track D → in progress / CLOSED at end |

---

### Task 1 — `BuildingCatalogSlice` v2 + extract + hash

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/building_catalog_slice.py`
- Modify: `django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py`
- Modify: `tests/unit/asteroid_lab/test_building_catalog_slice.py`

- [ ] **Step 1: Write failing test (geometry on slice)**

Replace `test_catalog_slice_excludes_footprint_and_connectors` with:

```python
def test_catalog_slice_v2_includes_variant_geometries() -> None:
    snap = AsteroidGameDataSnapshot(
        meta=_meta(),
        buildings=(
            BuildingSnapshot(
                canonical_id="bv:z",
                internal_name="z_miner",
                footprint_cells=(BuildingFootprintCell(1, 2, 0),),
                connectors=(
                    BuildingConnectorSnapshot(
                        0, "item_input", "East", "Regular", 0, 0, 0
                    ),
                ),
            ),
            BuildingSnapshot(
                canonical_id="bv:a",
                internal_name="a_miner",
                footprint_cells=(),
                connectors=(),
            ),
        ),
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:a"),),
    )
    sl = catalog_slice_from_snapshot(snap)
    assert sl.slice_version == "building_catalog_slice_v2"
    assert len(sl.variant_geometries) == 2
    z = next(g for g in sl.variant_geometries if g.canonical_id == "bv:z")
    assert z.footprint_cells == (BuildingFootprintCell(1, 2, 0),)
    assert len(z.connectors) == 1
    assert catalog_slice_hash(sl) != catalog_slice_hash(
        BuildingCatalogSlice(
            slice_version=sl.slice_version,
            transport_registry=sl.transport_registry,
            variants=sl.variants,
            variant_geometries=(),
        )
    )
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py::test_catalog_slice_v2_includes_variant_geometries -v
```

Expected: FAIL (`variant_geometries` missing or wrong version)

- [ ] **Step 3: Implement v2 slice + hash**

In `building_catalog_slice.py`:

- Set `SLICE_VERSION = "building_catalog_slice_v2"`
- Add `VariantGeometryCatalog` dataclass (import `BuildingFootprintCell`, `BuildingConnectorSnapshot` from `game_data_snapshot` contract module only)
- Add `variant_geometries` field to `BuildingCatalogSlice`
- In `catalog_slice_from_snapshot`, for each sorted building, append `VariantGeometryCatalog` using `validate_building_snapshot(b).footprint_cells` and `.connectors`

In `building_catalog_slice_hash.py`:

- Add `_geometry_dict` / include `variant_geometries` in `_canonical_payload`

Update all `BuildingCatalogSlice(...)` constructors in tests repo-wide that omit `variant_geometries` (grep `BuildingCatalogSlice(`).

- [ ] **Step 4: Run slice tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py -v
```

Expected: PASS (fix provenance tests expecting v1 string)

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/building_catalog_slice.py django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py tests/unit/asteroid_lab/test_building_catalog_slice.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py
git commit -m "feat(catalog): BuildingCatalogSlice v2 with variant geometries"
```

---

### Task 2 — `catalog_footprint_policy`

**Files:**
- Create: `django_apps/asteroid_lab/adapters/catalog_footprint_policy.py`
- Create: `tests/unit/asteroid_lab/test_catalog_footprint_policy.py`

- [ ] **Step 1: Write failing tests**

```python
"""Track D — catalog footprint policy."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_footprint_policy import (
    footprint_cells_for_variant,
    summarize_footprint_catalog,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    SLICE_VERSION,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingFootprintCell,
    TransportRegistryEntry,
)


def _slice_with_one_footprint() -> BuildingCatalogSlice:
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        variants=(VariantIdentity("bv:1", "miner_a"),),
        variant_geometries=(
            VariantGeometryCatalog(
                canonical_id="bv:1",
                internal_name="miner_a",
                footprint_cells=(BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 0)),
                connectors=(),
            ),
        ),
    )


def test_summarize_footprint_catalog_counts() -> None:
    metrics = summarize_footprint_catalog(_slice_with_one_footprint())
    assert metrics == {
        "catalog_variant_geometry_count": 1,
        "catalog_footprint_cell_count": 2,
        "catalog_connector_count": 0,
    }


def test_footprint_cells_for_variant_lookup() -> None:
    cells = footprint_cells_for_variant("bv:1", catalog_slice=_slice_with_one_footprint())
    assert len(cells) == 2


def test_footprint_cells_for_variant_missing_returns_empty() -> None:
    assert footprint_cells_for_variant("missing", catalog_slice=_slice_with_one_footprint()) == ()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_footprint_policy.py -v
```

- [ ] **Step 3: Implement policy**

```python
def summarize_footprint_catalog(slice: BuildingCatalogSlice) -> dict[str, int]:
    geometries = slice.variant_geometries
    return {
        "catalog_variant_geometry_count": len(geometries),
        "catalog_footprint_cell_count": sum(len(g.footprint_cells) for g in geometries),
        "catalog_connector_count": sum(len(g.connectors) for g in geometries),
    }


def footprint_cells_for_variant(
    canonical_id: str,
    *,
    catalog_slice: BuildingCatalogSlice,
) -> tuple[BuildingFootprintCell, ...]:
    for g in catalog_slice.variant_geometries:
        if g.canonical_id == canonical_id:
            return g.footprint_cells
    return ()
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_footprint_policy.py -v
python -m ruff check django_apps/asteroid_lab/adapters/catalog_footprint_policy.py
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/adapters/catalog_footprint_policy.py tests/unit/asteroid_lab/test_catalog_footprint_policy.py
git commit -m "feat(catalog): footprint policy summarize and lookup"
```

---

### Task 3 — RTTP output-only metrics

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/pipeline.py` (preferred) or `solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

- [ ] **Step 1: Write failing test**

In `test_solver_runtime_entry.py`, extend existing RTTP test with pinned game data:

```python
def test_solver_runtime_entry_rttp_emits_catalog_footprint_metrics() -> None:
    proj = m.AsteroidProject.objects.create(name="FootprintMetrics", slug="entry-fp-metrics")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    result = run_solver_runtime_with_pinned_game_data(int(proj.pk))
    assert result.ok is True
    steps = (result.solver_summary or {}).get("algorithm_steps") or []
    catalog_steps = [s for s in steps if isinstance(s, dict) and s.get("step_id") == "rttp.catalog_slice"]
    assert len(catalog_steps) == 1
    metrics = catalog_steps[0].get("metrics") or {}
    assert metrics.get("catalog_variant_geometry_count", 0) >= 0
    assert "catalog_footprint_cell_count" in metrics
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py::test_solver_runtime_entry_rttp_emits_catalog_footprint_metrics -v
```

- [ ] **Step 3: Wire metrics**

After `OptimizationInput` is built in `solver_runtime_entry` (or at start of `run_rttp_pipeline` when `inp.catalog_slice` is set — pass slice on `OptimizationInput` if already present, else thread `catalog_slice` kwarg into pipeline):

```python
from django_apps.asteroid_lab.adapters.catalog_footprint_policy import summarize_footprint_catalog

metrics = summarize_footprint_catalog(catalog_slice)
# append algorithm_steps entry: step_id="rttp.catalog_slice", metrics=metrics
```

Do **not** add fields to `OptimizationInput` unless already `catalog_slice` exists from B2 wiring — use the same `catalog_slice` object from entry.

- [ ] **Step 4: Run RTTP entry + narrow rttp tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py::test_solver_runtime_entry_rttp_emits_catalog_footprint_metrics tests/unit/asteroid_lab/test_solver_runtime_entry.py::test_solver_runtime_entry_rttp_returns_solver_run_id -v
```

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/optimization/pipeline.py django_apps/asteroid_lab/services/solver_runtime_entry.py tests/unit/asteroid_lab/test_solver_runtime_entry.py
git commit -m "feat(rttp): emit catalog footprint metrics on solver summary"
```

---

### Task 4 — Docs + plan sync

**Files:**
- Modify: `docs/domain/asteroid_game_data_snapshot.md`
- Modify: `documents/ai/current_plan.md`

- [ ] **Step 1: Add domain doc paragraph (Track D)**

**Track D (RTTP):** `BuildingCatalogSlice` v2 includes `variant_geometries` (footprint cells + connectors per variant). `catalog_footprint_policy` provides read-only summaries for solver metrics; placement validation from catalog is future work. Spec: `docs/superpowers/specs/2026-05-24-track-d-catalog-footprint-connector-design.md`.

- [ ] **Step 2: Narrow gate**

```bash
python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py tests/unit/asteroid_lab/test_catalog_footprint_policy.py tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v
```

- [ ] **Step 3: Commit**

```bash
git add docs/domain/asteroid_game_data_snapshot.md documents/ai/current_plan.md
git commit -m "docs: Track D catalog footprint slice v2"
```

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| Slice v2 + geometry extract | 1 |
| Hash + provenance version | 1 |
| `catalog_footprint_policy` | 2 |
| Output-only metrics | 3 |
| INV-D-04 arch test | 4 (boundary test unchanged) |
| Domain docs | 4 |

No TBD placeholders.

---

## Execution handoff

**Plan:** `docs/superpowers/plans/2026-05-24-track-d-catalog-footprint-connector.md`  
**Spec:** `docs/superpowers/specs/2026-05-24-track-d-catalog-footprint-connector-design.md`

1. **Subagent-Driven (recommended)** — fresh subagent per task  
2. **Inline Execution** — executing-plans with checkpoints

**Which approach?** User selected **subagent-driven-development**.
