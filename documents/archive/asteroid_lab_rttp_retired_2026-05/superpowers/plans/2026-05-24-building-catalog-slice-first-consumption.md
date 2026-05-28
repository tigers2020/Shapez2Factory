# Track B2 — Building Catalog Slice First Consumption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** RTTP resolves empty-map default `TransportKind` from a validated `BuildingCatalogSlice` and provenance v2 (`catalog_slice_hash` required); reconstruction stays topology authority.

**Architecture:** Allowlist slice DTO + `catalog_slice_hash` (includes `slice_version`); provenance v2 ten-key wire; `resolve_default_asteroid_transport_kind` policy (no registry tuple-order); entry validates hash before `SolverRun`; T1 only in this PR (T2 next PR).

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, `StrEnum`, pytest-django.

**Approved spec:** [`2026-05-24-building-catalog-slice-first-consumption-design.md`](../specs/2026-05-24-building-catalog-slice-first-consumption-design.md)

**Worktree (recommended):** `f:\Python_Projects\shapez2Factory\.worktrees\building-catalog-slice-b2` on branch `feature/building-catalog-slice-b2`.

**Non-goals:** T2 cell-level registry resolution; footprint/macro catalog authority; full gate Task 7C unless PR closing.

**Merge gate:** ADR-004 B2 allowlist subsection MUST land in same PR before or with B2-3 (Task 5).

**Execution amendments (2026-05-24, Principal Solver):**

| Item | Rule |
|------|------|
| Parsers | `parse_provenance_config` = v2 strict; `parse_provenance_config_v1` = historical; RTTP v2 only |
| Reproducibility | `reproducibility_key_v1()` 3-tuple; `reproducibility_key()` 5-tuple |
| T1 policy | Belt channel in registry → `SHAPE_BELT`; pipe rows do not block asteroid default |
| Runtime | `CATALOG_SLICE_REQUIRED` separate from `CATALOG_SLICE_HASH_MISMATCH` |

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/contracts/building_catalog_slice.py` | **CREATE** — `BuildingCatalogSlice`, `VariantIdentity`, `catalog_slice_from_snapshot` |
| `django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py` | **CREATE** — `catalog_slice_hash()` |
| `django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py` | **MODIFY** — v2 fields, `parse_provenance_config_v1`, v2 strict parser |
| `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` | **CREATE** — `resolve_default_asteroid_transport_kind`, error enum |
| `django_apps/asteroid_lab/optimization/input_contracts.py` | **MODIFY** — `catalog_slice` on `OptimizationInput` |
| `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | **MODIFY** — T1 catalog path when slice present |
| `django_apps/web/services/asteroid_game_data_snapshot.py` | **MODIFY** — build slice + v2 provenance |
| `django_apps/asteroid_lab/services/solver_runtime_entry.py` | **MODIFY** — slice validation, pass slice, new error codes |
| `django_apps/asteroid_lab/services/solver_run_config_keys.py` | **MODIFY** — document v2 provenance keys |
| `tests/unit/asteroid_lab/test_building_catalog_slice.py` | **CREATE** |
| `tests/unit/asteroid_lab/test_building_catalog_slice_hash.py` | **CREATE** |
| `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py` | **MODIFY** — v2 + v1 historical |
| `tests/unit/asteroid_lab/test_catalog_transport_policy.py` | **CREATE** |
| `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | **MODIFY** — T1 parity + catalog path |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | **MODIFY** — hash mismatch, catalog required |
| `tests/unit/architecture/test_catalog_consumption_boundaries.py` | **CREATE** |
| `docs/adr/ADR-004-game-data-snapshot-boundary.md` | **MODIFY** — B2 allowlist |
| `docs/domain/asteroid_game_data_snapshot.md` | **MODIFY** — slice + provenance v2 |

---

## Wire format (provenance v2)

Ten keys in `SolverRun.config_json["game_data_snapshot_provenance"]`:

```json
{
  "snapshot_schema_version": "game_data_snapshot_v1",
  "rule_version": "asteroid_v0",
  "data_revision": "<manifest_self_hash>",
  "import_batch_id": "42",
  "content_hash": "<64-char hex>",
  "game_version": "<game_version>",
  "db_alias": "default",
  "built_at_utc": "2026-05-24T12:00:00Z",
  "catalog_slice_version": "building_catalog_slice_v1",
  "catalog_slice_hash": "<64-char hex>"
}
```

---

### Task 1: `BuildingCatalogSlice` contract

**Files:**
- Create: `django_apps/asteroid_lab/contracts/building_catalog_slice.py`
- Test: `tests/unit/asteroid_lab/test_building_catalog_slice.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/asteroid_lab/test_building_catalog_slice.py
from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    VariantIdentity,
    BuildingCatalogSlice,
    catalog_slice_from_snapshot,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
)


def _meta():
    return build_snapshot_meta(
        data_revision="rev",
        db_alias="default",
        built_at_utc="2026-05-24T00:00:00Z",
        content_hash="a" * 64,
        game_version="1.0",
    )


def test_catalog_slice_excludes_footprint_and_connectors() -> None:
    snap = AsteroidGameDataSnapshot(
        meta=_meta(),
        buildings=(
            BuildingSnapshot(
                canonical_id="bv:z",
                internal_name="z",
                footprint_cells=(BuildingFootprintCell(1, 2, 0),),
                connectors=(
                    BuildingConnectorSnapshot(
                        0, "item_input", "East", "Regular", 0, 0, 0
                    ),
                ),
            ),
            BuildingSnapshot(
                canonical_id="bv:a",
                internal_name="a",
                footprint_cells=(),
                connectors=(),
            ),
        ),
        transport_registry=(TransportRegistryEntry("z_kind", "belt", "bv:a"),),
    )
    sl = catalog_slice_from_snapshot(snap)
    assert sl.slice_version == SLICE_VERSION
    assert sl.transport_registry[0].transport_kind == "z_kind"
    assert sl.variants == (
        VariantIdentity("bv:a", "a"),
        VariantIdentity("bv:z", "z"),
    )
    assert not hasattr(sl, "footprint_cells")
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py::test_catalog_slice_excludes_footprint_and_connectors -v`  
Expected: FAIL — `catalog_slice_from_snapshot` not defined

- [ ] **Step 3: Implement minimal slice + extract**

```python
# django_apps/asteroid_lab/contracts/building_catalog_slice.py
from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    AsteroidGameDataSnapshot,
    TransportRegistryEntry,
)

SLICE_VERSION = "building_catalog_slice_v1"


@dataclass(frozen=True, slots=True)
class VariantIdentity:
    canonical_id: str
    internal_name: str


@dataclass(frozen=True, slots=True)
class BuildingCatalogSlice:
    slice_version: str
    transport_registry: tuple[TransportRegistryEntry, ...]
    variants: tuple[VariantIdentity, ...]


def catalog_slice_from_snapshot(snapshot: AsteroidGameDataSnapshot) -> BuildingCatalogSlice:
    variants = tuple(
        VariantIdentity(canonical_id=b.canonical_id, internal_name=b.internal_name)
        for b in sorted(
            snapshot.buildings,
            key=lambda b: (b.internal_name, b.canonical_id),
        )
    )
    registry = tuple(
        sorted(snapshot.transport_registry, key=lambda e: e.transport_kind)
    )
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=registry,
        variants=variants,
    )
```

- [ ] **Step 4: Run test — expect PASS**

Run: `python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py -v`

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/building_catalog_slice.py tests/unit/asteroid_lab/test_building_catalog_slice.py
git commit -m "feat(asteroid_lab): add BuildingCatalogSlice contract"
```

---

### Task 2: `catalog_slice_hash`

**Files:**
- Create: `django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py`
- Test: `tests/unit/asteroid_lab/test_building_catalog_slice_hash.py`

- [ ] **Step 1: Write failing hash stability test**

```python
# tests/unit/asteroid_lab/test_building_catalog_slice_hash.py
from __future__ import annotations

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantIdentity,
    SLICE_VERSION,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry


def test_catalog_slice_hash_includes_slice_version_and_order_invariant() -> None:
    t1 = TransportRegistryEntry("a", "belt", "bv:1")
    t2 = TransportRegistryEntry("z", "belt", "bv:2")
    v1 = VariantIdentity("bv:1", "a")
    v2 = VariantIdentity("bv:2", "z")
    s1 = BuildingCatalogSlice(SLICE_VERSION, (t2, t1), (v2, v1))
    s2 = BuildingCatalogSlice(SLICE_VERSION, (t1, t2), (v1, v2))
    assert catalog_slice_hash(s1) == catalog_slice_hash(s2)
    assert len(catalog_slice_hash(s1)) == 64
```

- [ ] **Step 2: Run — expect FAIL**

Run: `python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice_hash.py -v`

- [ ] **Step 3: Implement hash**

```python
# django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py
from __future__ import annotations

import hashlib
import json

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
)


def _variant_dict(v) -> dict[str, str]:
    return {"canonical_id": v.canonical_id, "internal_name": v.internal_name}


def _transport_dict(e) -> dict[str, str]:
    return {
        "building_variant_canonical_id": e.building_variant_canonical_id,
        "transport_category": e.transport_category,
        "transport_kind": e.transport_kind,
    }


def _canonical_payload(sl: BuildingCatalogSlice) -> dict[str, object]:
    registry = sorted(sl.transport_registry, key=lambda e: e.transport_kind)
    variants = sorted(sl.variants, key=lambda v: (v.internal_name, v.canonical_id))
    return {
        "slice_version": sl.slice_version,
        "transport_registry": [_transport_dict(e) for e in registry],
        "variants": [_variant_dict(v) for v in variants],
    }


def catalog_slice_hash(sl: BuildingCatalogSlice) -> str:
    blob = json.dumps(_canonical_payload(sl), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
```

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py tests/unit/asteroid_lab/test_building_catalog_slice_hash.py
git commit -m "feat(asteroid_lab): deterministic catalog_slice_hash"
```

---

### Task 3: Provenance v2 + historical v1 parser

**Files:**
- Modify: `django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py`
- Modify: `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py`

- [ ] **Step 1: Write failing v2 round-trip test**

```python
def test_provenance_v2_requires_catalog_fields(
    minimal_snapshot_with_slice,
) -> None:
    from django_apps.asteroid_lab.contracts.building_catalog_slice import (
        catalog_slice_from_snapshot,
    )
    from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
        catalog_slice_hash,
    )

    snap = minimal_snapshot_with_slice
    sl = catalog_slice_from_snapshot(snap)
    prov = provenance_from_snapshot(
        snap, import_batch_id=1, catalog_slice=sl
    )
    assert prov.catalog_slice_version == "building_catalog_slice_v1"
    assert prov.catalog_slice_hash == catalog_slice_hash(sl)
    wire = provenance_to_config_dict(prov)
    assert len(wire) == 10
    parsed = parse_provenance_config(wire)
    assert parsed.catalog_slice_hash == prov.catalog_slice_hash


def test_parse_provenance_v1_historical_eight_keys() -> None:
    from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
        parse_provenance_config_v1,
    )

    payload = {
        "snapshot_schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "data_revision": "rev-hash-001",
        "import_batch_id": "1",
        "content_hash": "a" * 64,
        "game_version": "9.9.9",
        "db_alias": "default",
        "built_at_utc": "2026-05-24T00:00:00Z",
    }
    parsed = parse_provenance_config_v1(payload)
    assert parsed.import_batch_id == 1
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Extend provenance module**

Changes (implement in file):

1. Add to `GameDataSnapshotProvenance`:
   - `catalog_slice_version: str`
   - `catalog_slice_hash: str`
2. `_REQUIRED_KEYS_V2` = v1 keys | `{catalog_slice_version, catalog_slice_hash}`
3. `parse_provenance_config` → strict 10 keys (rename internal v1 set to `_REQUIRED_KEYS_V1`)
4. `parse_provenance_config_v1` → 8 keys for historical readback only
5. `provenance_from_snapshot(..., catalog_slice: BuildingCatalogSlice)` — required for builder
6. Validate `catalog_slice_version == SLICE_VERSION` and 64-hex `catalog_slice_hash`
7. Extend `reproducibility_key()` → 5-tuple including catalog fields

- [ ] **Step 4: Update existing provenance tests** to pass `catalog_slice` into `provenance_from_snapshot` or use test helper building minimal slice.

- [ ] **Step 5: Run**

Run: `python -m pytest tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py -v`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(asteroid_lab): provenance v2 with required catalog_slice_hash"
```

---

### Task 4: ADR-004 + domain doc (before B2-3 behavior merge)

**Files:**
- Modify: `docs/adr/ADR-004-game-data-snapshot-boundary.md`
- Modify: `docs/domain/asteroid_game_data_snapshot.md`

- [ ] **Step 1: Add ADR subsection** `### Building catalog slice (Track B2, 2026-05-24)` with allowlist paragraph from spec.

- [ ] **Step 2: Add domain sections** `BuildingCatalogSlice`, `catalog_slice_hash`, provenance v2 table, T1 policy reference.

- [ ] **Step 3: Commit**

```bash
git commit -m "docs: ADR-004 Track B2 catalog slice allowlist"
```

---

### Task 5: `resolve_default_asteroid_transport_kind` (T1 policy)

**Files:**
- Create: `django_apps/asteroid_lab/adapters/catalog_transport_policy.py`
- Test: `tests/unit/asteroid_lab/test_catalog_transport_policy.py`

- [ ] **Step 1: Write failing tests**

```python
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    CatalogTransportErrorCode,
    CatalogTransportUnresolvedError,
    resolve_default_asteroid_transport_kind,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    SLICE_VERSION,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def test_resolve_default_prefers_shape_belt_when_belt_category_present() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    assert (
        resolve_default_asteroid_transport_kind(sl) is TransportKind.SHAPE_BELT
    )


def test_resolve_default_fails_closed_when_ambiguous() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (
            TransportRegistryEntry("a", "belt", "bv:1"),
            TransportRegistryEntry("b", "pipe", "bv:2"),
        ),
        (),
    )
    with pytest.raises(CatalogTransportUnresolvedError) as exc:
        resolve_default_asteroid_transport_kind(sl)
    assert exc.value.code == CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Implement policy** (use `TRANSPORT_CATEGORY_TO_KIND` map; never index `transport_registry[0]`)

- [ ] **Step 4: Run — expect PASS**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(asteroid_lab): catalog default transport policy (T1)"
```

---

### Task 6: `OptimizationInput` + reconstruction adapter T1

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/input_contracts.py`
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Modify: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`

- [ ] **Step 1: Add failing test — greenfield + catalog → SHAPE_BELT**

```python
def test_greenfield_default_transport_uses_catalog_slice() -> None:
    from django_apps.asteroid_lab.contracts.building_catalog_slice import (
        BuildingCatalogSlice,
        SLICE_VERSION,
    )
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        TransportRegistryEntry,
    )

    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    inp = optimization_input_from_reconstruction(
        ReconstructionResult(cells=cells),
        catalog_slice=sl,
    )
    assert inp.transport_kind is TransportKind.SHAPE_BELT
```

- [ ] **Step 2: Run — expect FAIL**

- [ ] **Step 3: Add `catalog_slice` field to `OptimizationInput`**

- [ ] **Step 4: In `optimization_input_from_reconstruction`**, when `not existing_transport` and `catalog_slice is not None`, set `transport_kind = resolve_default_asteroid_transport_kind(catalog_slice)`; when `catalog_slice is None`, keep `_default_transport_kind` for unit tests only.

- [ ] **Step 5: Run adapter tests — expect PASS**

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(asteroid_lab): T1 default transport from catalog slice"
```

---

### Task 7: Web builder emits slice + provenance v2

**Files:**
- Modify: `django_apps/web/services/asteroid_game_data_snapshot.py`
- Modify: `tests/unit/web/test_asteroid_game_data_snapshot.py` (if present; else create narrow test)

- [ ] **Step 1: Extend `GameDataSnapshotBuildResult`**

```python
@dataclass(frozen=True, slots=True)
class GameDataSnapshotBuildResult:
    snapshot: AsteroidGameDataSnapshot
    provenance: GameDataSnapshotProvenance
    catalog_slice: BuildingCatalogSlice
```

- [ ] **Step 2: In `build_asteroid_game_data_snapshot_with_provenance`**, after snapshot build:

```python
catalog_slice = catalog_slice_from_snapshot(snapshot)
provenance = provenance_from_snapshot(
    snapshot,
    import_batch_id=int(batch.pk),
    catalog_slice=catalog_slice,
)
```

- [ ] **Step 3: Test** — `catalog_slice_hash` on provenance matches `catalog_slice_hash(catalog_slice)`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(web): build catalog slice with provenance v2"
```

---

### Task 8: Runtime entry — validation, wiring, error codes

**Files:**
- Modify: `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- Modify: `tests/unit/asteroid_lab/test_solver_runtime_entry.py`

- [ ] **Step 1: Add error codes**

```python
class SolverRuntimeEntryErrorCode(StrEnum):
    ...
    CATALOG_SLICE_HASH_MISMATCH = "catalog_slice_hash_mismatch"
    CATALOG_TRANSPORT_UNRESOLVED = "catalog_transport_unresolved"
```

- [ ] **Step 2: Add helper `_validate_catalog_slice_for_run`**

```python
def _validate_catalog_slice_for_run(
    *,
    snapshot: AsteroidGameDataSnapshot,
    provenance: GameDataSnapshotProvenance,
    catalog_slice: BuildingCatalogSlice,
) -> None:
    from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
        catalog_slice_hash,
    )

    expected = catalog_slice_hash(catalog_slice)
    if provenance.catalog_slice_hash != expected:
        raise ValueError("catalog_slice_hash mismatch")
    extracted = catalog_slice_from_snapshot(snapshot)
    if catalog_slice_hash(extracted) != expected:
        raise ValueError("catalog slice extract mismatch")
```

- [ ] **Step 3: Change `run_solver_runtime_for_project`** to accept `catalog_slice: BuildingCatalogSlice | None` (or take full `GameDataSnapshotBuildResult`).

- [ ] **Step 4: In `_run_rttp_solver_for_map_input`**, before `create_solver_run`:

- validate catalog slice vs provenance
- wrap `optimization_input_from_reconstruction(..., catalog_slice=catalog_slice)`
- catch `CatalogTransportUnresolvedError` → `_failure_result(..., CATALOG_TRANSPORT_UNRESOLVED)`

- [ ] **Step 5: Update HTTP + `run_solver` command** to pass `game_data_build.catalog_slice`.

- [ ] **Step 6: Write failing entry tests** for hash mismatch and missing catalog fields on v2.

- [ ] **Step 7: Run**

Run: `python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/integration/web/test_asteroid_run_solver.py -v`

- [ ] **Step 8: Commit**

```bash
git commit -m "feat(asteroid_lab): wire catalog slice into RTTP entry (T1)"
```

---

### Task 9: Architecture guard

**Files:**
- Create: `tests/unit/architecture/test_catalog_consumption_boundaries.py`

- [ ] **Step 1: Test optimization package does not import footprint types**

```python
_FORBIDDEN_IN_OPTIMIZATION = frozenset({
    "BuildingFootprintCell",
    "BuildingConnectorSnapshot",
    "BuildingSnapshot",
})

def test_optimization_modules_do_not_import_building_geometry_types():
    root = _REPO_ROOT / "django_apps" / "asteroid_lab" / "optimization"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        # assert no ImportFrom game_data_snapshot importing forbidden names
```

- [ ] **Step 2: Run architecture tests**

Run: `python -m pytest tests/unit/architecture/test_catalog_consumption_boundaries.py tests/unit/architecture/test_django_app_import_boundaries.py -v`

- [ ] **Step 3: Commit**

```bash
git commit -m "test(arch): catalog consumption geometry import guard"
```

---

### Task 10: Narrow gate + RTTP test helper update

**Files:**
- Modify: `tests/unit/asteroid_lab/_runtime_game_data.py` (pass catalog slice from build result)

- [ ] **Step 1: Update `run_solver_runtime_with_pinned_game_data`** to pass `catalog_slice` from `build_asteroid_game_data_snapshot_with_provenance()`.

- [ ] **Step 2: Run narrow gate**

```powershell
python -m pytest tests/unit/asteroid_lab/test_building_catalog_slice.py tests/unit/asteroid_lab/test_building_catalog_slice_hash.py tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_optimization_input_adapter.py tests/unit/asteroid_lab/test_solver_runtime_entry.py tests/unit/architecture/test_catalog_consumption_boundaries.py -v
python -m ruff check django_apps/asteroid_lab/contracts/building_catalog_slice.py django_apps/asteroid_lab/contracts/building_catalog_slice_hash.py django_apps/asteroid_lab/contracts/game_data_snapshot_provenance.py django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/optimization/input_contracts.py django_apps/asteroid_lab/optimization/reconstruction_adapter.py django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/services/asteroid_game_data_snapshot.py
```

- [ ] **Step 3: Fix any RTTP integration tests** broken by provenance v2 requirement.

Run: `python -m pytest tests/integration/web/test_asteroid_run_solver.py tests/integration/asteroid_lab/test_rttp_run_solver_macro_integration.py -v`

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| `BuildingCatalogSlice` DTO | Task 1 |
| `catalog_slice_hash` includes `slice_version` | Task 2 |
| Provenance v2 required, v1 historical parse | Task 3 |
| ADR B2 allowlist | Task 4 |
| T1 policy, no tuple order | Task 5 |
| OptimizationInput + adapter | Task 6 |
| Single builder | Task 7 |
| Entry hash gate + error enums | Task 8 |
| Arch guard INV-CAT-05/06 | Task 9 |
| RTTP test helper | Task 10 |

No TBD placeholders in task steps above.

---

## Implementation status

| Task | Status |
|------|--------|
| Task 1 — Slice contract | [x] |
| Task 2 — catalog_slice_hash | [x] |
| Task 3 — Provenance v2 | [x] |
| Task 4 — ADR + domain | [x] |
| Task 5 — T1 policy | [x] |
| Task 6 — Adapter T1 | [x] |
| Task 7 — Web builder | [x] |
| Task 8 — Runtime entry | [x] |
| Task 9 — Arch guard | [x] |
| Task 10 — Narrow gate | [x] |

---

## Execution handoff

Plan saved to [`docs/superpowers/plans/2026-05-24-building-catalog-slice-first-consumption.md`](2026-05-24-building-catalog-slice-first-consumption.md).

Spec saved to [`docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md`](../specs/2026-05-24-building-catalog-slice-first-consumption-design.md).

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

Which approach?
