# B2-T2 — Per-Cell Transport Resolution

**Status:** Approved 2026-05-24 (Approach 1; duplicate-key conflict fail-closed)  
**Scope:** B2-T2 only  
**Parent track:** [Building Catalog Slice First Consumption](2026-05-24-building-catalog-slice-first-consumption-design.md)  
**Implementation plan:** [`2026-05-24-b2-t2-per-cell-transport-resolution.md`](../plans/2026-05-24-b2-t2-per-cell-transport-resolution.md)  
**Next track (blocked until T2 on `master`):** [B2-T3 transport-aware route domain](2026-05-24-b2-t3-transport-aware-route-domain-design.md)

**Approved approach:** Approach 1 — `catalog_transport_policy` lookup/resolve + `reconstruction_adapter` wiring. `BuildingCatalogSlice` stays a frozen DTO (no methods).

---

## 1. Problem / goal / success criteria

### Problem

Reconstruction transport tiles carry `transport_kind` wire strings from the game-data registry (`space_belt`, `space_pipe`, …) or from the reconstruction classifier as domain enum values (`shape_belt`, `fluid_pipe`).

Today `reconstruction_adapter._existing_transport` only retains cells where `_parse_transport_kind` matches a `TransportKind` enum value. Registry wire strings return `None` and the cell is **silently skipped**. On the RTTP path this drops real existing transport from `OptimizationInput`, understates `existing_trunk_cells`, and can let the pipeline proceed with wrong trunk/goal assumptions.

B2-T1 already resolves **greenfield default** transport when `existing_transport` is empty. T2 closes the gap for **maps that already have transport tiles**.

### Goal

RTTP must resolve every reconstruction transport cell to a domain `TransportKind` via the catalog slice registry (or fail closed), so downstream tracks (especially B2-T3) consume a complete, correctly typed `existing_transport_cells` set.

### Success criteria

```text
RTTP path (catalog_slice non-None): every reconstruction transport tile resolves to a domain TransportKind
  or the run fails closed with CATALOG_TRANSPORT_UNRESOLVED before optimization proceeds.
T1 greenfield default (empty existing_transport) behavior unchanged.
B2-T3 can consume fully resolved ExistingTransportCell rows (no silent drops).
Reconstruction narrow gate and existing catalog/RTTP unit tests stay green.
```

---

## 2. Per-cell resolution policy

### Registry lookup (`transport_kind_lookup_from_slice`)

Build once per `optimization_input_from_reconstruction` call when `catalog_slice is not None`.

Iterate `catalog_slice.transport_registry` in slice canonical order (as stored on the frozen slice).

For each entry:

1. `category = entry.transport_category.strip().lower()`
2. `kind = TRANSPORT_CATEGORY_TO_KIND.get(category)` — same map as T1 (`belt` → `SHAPE_BELT`, `pipe` → `FLUID_PIPE`)
3. Unknown category → skip row (same as T1)
4. `key = entry.transport_kind`
5. If `key` already in lookup:
   - **Same resolved `TransportKind`** → overwrite with `kind` (deterministic **last-wins** in slice order)
   - **Conflicting resolved `TransportKind`** → **`CatalogTransportUnresolvedError`** at lookup build time (fail-closed)
6. Else → `lookup[key] = kind`

Examples:

```text
dup → belt, dup → belt     OK (last-wins, same kind)
dup → belt, dup → pipe     FAIL-CLOSED (conflicting TransportKind)
```

### Per-cell resolution (`resolve_cell_transport_kind`)

For wire string `raw`:

| Step | Condition | Result |
|------|-----------|--------|
| 1 | `raw` matches `TransportKind` enum value | Return that kind (**domain passthrough**; beats registry) |
| 2 | `catalog_slice is None` | Return `None` → adapter skips cell (**legacy/test only**; see §3) |
| 3 | `raw` in lookup table | Return mapped kind |
| 4 | `catalog_slice` present, not in lookup | `CatalogTransportUnresolvedError` (message includes `raw` and optional `coord`) |

Optional `lookup` argument avoids rebuilding the table per cell.

### `catalog_slice is None` (legacy / test only)

The `catalog_slice is None` branch keeps `_parse_transport_kind` + silent skip for **adapter unit-test compatibility only**.

**Solver runtime B2 path MUST pass non-None `catalog_slice`.** RTTP entry already requires slice + provenance hash match; it must not call `optimization_input_from_reconstruction` without slice.

---

## 3. Component and data flow

```text
catalog_transport_policy.py
  transport_kind_lookup_from_slice(slice)  → dict[str, TransportKind] | raises on conflict
  resolve_cell_transport_kind(raw, catalog_slice, lookup?, coord?)

reconstruction_adapter.py
  optimization_input_from_reconstruction(..., catalog_slice)
    lookup = transport_kind_lookup_from_slice(slice)   # once; if slice set
    existing_transport = _existing_transport(by_coord, catalog_slice=slice)
      per transport cell → resolve_cell_transport_kind(...)

solver_runtime_entry.py  (no T2 code changes)
  validate slice + provenance
  → optimization_input_from_reconstruction(..., catalog_slice=slice)   # MUST

OptimizationInput.existing_transport_cells  → fully resolved kinds for RTTP
```

**Layer rules:**

- Policy in `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` (no `game_data` import).
- Adapter wires policy; `optimization/*` does not import `TransportRegistryEntry` or build registry maps.
- T1 `resolve_default_asteroid_transport_kind` unchanged when `existing_transport` is empty.

---

## 4. Error handling and test matrix

### Error handling

| Situation | Error | Entry mapping |
|-----------|--------|----------------|
| T1: no belt channel in registry | `CatalogTransportUnresolvedError` | `CATALOG_TRANSPORT_UNRESOLVED` |
| T2: per-cell wire not resolved | `CatalogTransportUnresolvedError` (optional `coord` in message) | same |
| T2: duplicate registry key, conflicting kinds | `CatalogTransportUnresolvedError` at lookup build | same |

```python
CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED  # existing StrEnum
```

`solver_runtime_entry` mapping is **unchanged** in T2 PR.

### Test matrix

| Test | Layer | Asserts |
|------|-------|---------|
| `test_lookup_maps_registry_transport_kind_to_domain_kind` | policy | `space_belt` → `SHAPE_BELT` |
| `test_duplicate_registry_key_same_kind_last_wins` | policy | same kind duplicates → last-wins |
| `test_duplicate_registry_key_conflicting_kind_raises` | policy | belt + pipe on same key → raise |
| `test_resolve_cell_prefers_domain_enum_over_registry` | policy | enum beats registry row for same string |
| `test_resolve_cell_uses_registry_key_when_not_domain_enum` | policy | registry wire resolves |
| `test_resolve_cell_without_catalog_returns_none_for_unknown` | policy | legacy `None` when no slice |
| `test_resolve_cell_with_catalog_raises_when_unresolved` | policy | fail-closed + coord in message |
| `test_existing_transport_resolves_registry_key_via_catalog_slice` | adapter | pipe wire → `FLUID_PIPE` in input |
| `test_unresolved_transport_cell_fails_when_catalog_slice_present` | adapter | empty registry + transport tile → raise |
| `test_domain_enum_transport_kind_precedence_over_registry` | adapter | classifier enum wins over bad registry row |

**Regression (must stay green):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Plus: `test_catalog_consumption_boundaries.py`; `test_building_catalog_slice.py`; `test_solver_runtime_entry.py` (catalog/transport cases).

---

## 5. Out of scope

| Area | Reason |
|------|--------|
| **B2-T3** trunk/blocked partition, route domain, route probe | After T2 on `master` |
| **Macro** compiler, macro E2E, selection, fitness, regret | PAUSED / forbidden |
| **Route-domain / probe** changes | B2-T3 |
| **Replay** frames / ORM → solver algorithm input | Forbidden |
| `_default_transport_kind` heuristic when map has existing transport | T2 is per-cell only |
| Validation relax / new bypass | Forbidden |
| `BuildingCatalogSlice` shape / provenance v2 wire | B2-1 closed |
| `solver_runtime_entry` new error codes | Existing mapping sufficient |
| **Ops smoke B** (real slug with existing transport) | Follow-up after merge; not PR gate |

---

## 6. Invariants

| ID | Rule |
|----|------|
| INV-T2-01 | RTTP entry always passes non-None `catalog_slice`; unresolved transport tile fails before `create_solver_run` |
| INV-T2-02 | `catalog_transport_policy` does not import `game_data` |
| INV-T2-03 | `optimization/*` does not import `TransportRegistryEntry` or build registry maps |
| INV-T2-04 | T1 `resolve_default_asteroid_transport_kind` unchanged for empty `existing_transport` |
| INV-T2-05 | Lookup iteration uses canonical slice order only |
| INV-T2-06 | Duplicate registry key + conflicting `TransportKind` → fail-closed at lookup build |
| INV-T2-07 | Duplicate registry key + same `TransportKind` → deterministic last-wins allowed |
| INV-T2-08 | Domain enum `transport_kind` on a cell takes precedence over registry mapping for that string |

---

## 7. Self-review checklist

| Check | Status |
|-------|--------|
| Scope is B2-T2 only (no T3/macro/route/probe/replay) | Pass |
| Approach 1: policy + adapter; slice stays DTO | Pass |
| Duplicate key: same kind → last-wins | Pass (§2) |
| Duplicate key: conflicting kind → fail-closed | Pass (§2, INV-T2-06) |
| `catalog_slice is None` documented as legacy/test only | Pass (§2, §3) |
| Runtime B2 path must pass `catalog_slice` | Pass (§2, INV-T2-01) |
| Per-cell order: enum → legacy None → lookup → fail-closed | Pass (§2) |
| T1 greenfield default unchanged | Pass (INV-T2-04) |
| Error code reuses `CATALOG_TRANSPORT_UNRESOLVED` | Pass (§4) |
| Test matrix covers conflict + enum precedence + adapter | Pass (§4) |
| No placeholders / TBD | Pass |
| Internal consistency (lookup conflict vs per-cell fail-closed) | Pass |
| Plan file references this spec | Pass |

**Drift vs prior gatekeeper approval:** None. Spec reorganized into required sections 1–7; policy unchanged from approved brainstorming corrections.

---

## Documentation (implementation PR)

- `docs/domain/asteroid_game_data_snapshot.md` — T2 paragraph
- Parent B2 design — T2 section cross-link to this file

## Follow-up (post-merge)

- Ops smoke B on slug with existing transport registry wires
- B2-T3 transport-aware route domain
