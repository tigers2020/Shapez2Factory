# B2-T2 — Per-Cell Transport Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** RTTP resolves each reconstruction transport cell’s `transport_kind` wire string through `BuildingCatalogSlice.transport_registry` (category → `TransportKind`), while T1 empty-map default behavior stays unchanged.

**Architecture:** Extend `catalog_transport_policy` with a frozen registry lookup (`transport_kind` registry key → `TransportKind` via `transport_category`). `reconstruction_adapter._existing_transport` uses that lookup when `catalog_slice` is set; domain enum strings (`shape_belt`, `fluid_pipe`) pass through unchanged. Unresolved transport tiles on the RTTP path raise `CatalogTransportUnresolvedError` (already mapped to `CATALOG_TRANSPORT_UNRESOLVED` in `solver_runtime_entry`). No changes to macro, selection, validation, route-domain geometry, or replay-as-input.

**Tech Stack:** Python 3.12, Django 5, frozen dataclasses, `StrEnum`, pytest.

**Approved spec (parent):** [`2026-05-24-building-catalog-slice-first-consumption-design.md`](../specs/2026-05-24-building-catalog-slice-first-consumption-design.md) — T2 bullet; this plan is the concrete T2 policy.

**Predecessor plan (CLOSED):** [`2026-05-24-building-catalog-slice-first-consumption.md`](2026-05-24-building-catalog-slice-first-consumption.md)

**Worktree (recommended):** `f:\Python_Projects\shapez2Factory\.worktrees\b2-t2-per-cell-transport` on branch `feature/b2-t2-per-cell-transport`.

---

## Out of scope (PR gate — do not touch)

| Area | Reason |
|------|--------|
| `optimization/macros/**`, macro compiler, macro E2E | RTTP macro track PAUSED |
| `optimization/selection/**`, fitness, regret | Forbidden |
| RTTP validation relax / new bypass | Forbidden |
| Footprint, connector, full placement geometry | Track D |
| Replay frames / ORM → solver algorithm input | Forbidden |
| `RouteDomainSnapshotBuilder`, route probe | Future track |
| `BuildingCatalogSlice` shape / provenance v2 wire | B2-1 closed |
| `_default_transport_kind` heuristic when map has existing transport | T2 is per-cell only; pipeline default unchanged |

**Regression gates (must stay green, no edits unless broken by T2):**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

---

## T2 policy (normative)

### Lookup table

Build once per `optimization_input_from_reconstruction` call when `catalog_slice is not None`:

```text
registry_key = TransportRegistryEntry.transport_kind   # e.g. "space_belt"
category     = entry.transport_category.strip().lower() # "belt" | "pipe"
TransportKind = TRANSPORT_CATEGORY_TO_KIND[category]  # same map as T1
```

- Unknown `transport_category` → row omitted from lookup (same as T1 skip).
- Duplicate `registry_key` in slice → **last wins** in canonical registry order (`transport_kind` sort on slice); document in test; real imports should not duplicate keys.

### Per-cell resolution order

For each reconstruction cell where `_is_reconstruction_transport_cell(cell)` is true:

1. If `cell.transport_kind` matches a `TransportKind` enum value (`shape_belt`, `fluid_pipe`) → use it (**domain passthrough**; reconstruction classifier output).
2. Else if `catalog_slice is not None` and `cell.transport_kind` is a registry key in lookup → use mapped `TransportKind`.
3. Else if `catalog_slice is not None` → **fail-closed** `CatalogTransportUnresolvedError(CATALOG_TRANSPORT_UNRESOLVED, message includes coord + raw string)`.
4. Else (`catalog_slice is None`, unit tests) → **skip cell** (current silent behavior).

### Invariants

| ID | Rule |
|----|------|
| INV-T2-01 | RTTP entry always passes non-None `catalog_slice`; unresolved transport tile fails before `create_solver_run` |
| INV-T2-02 | `catalog_transport_policy` does not import `game_data` |
| INV-T2-03 | `optimization/*` does not import `TransportRegistryEntry` or build registry maps (adapter-only) |
| INV-T2-04 | T1 `resolve_default_asteroid_transport_kind` unchanged for empty `existing_transport` |
| INV-T2-05 | Registry tuple order does not affect lookup semantics (canonical slice order only) |

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/asteroid_lab/adapters/catalog_transport_policy.py` | **MODIFY** — `transport_kind_lookup_from_slice`, `resolve_cell_transport_kind` |
| `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` | **MODIFY** — T2 path in `_existing_transport` |
| `tests/unit/asteroid_lab/test_catalog_transport_policy.py` | **MODIFY** — lookup + resolve unit tests |
| `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | **MODIFY** — registry-key cells + fail-closed |
| `docs/domain/asteroid_game_data_snapshot.md` | **MODIFY** — T2 paragraph under B2 slice section |

**No changes:** `solver_runtime_entry.py` (already catches `CatalogTransportUnresolvedError`), macro/selection/validation modules.

---

### Task 1: Registry lookup + cell resolver (`catalog_transport_policy`)

**Files:**
- Modify: `django_apps/asteroid_lab/adapters/catalog_transport_policy.py`
- Test: `tests/unit/asteroid_lab/test_catalog_transport_policy.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/unit/asteroid_lab/test_catalog_transport_policy.py`:

```python
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    transport_kind_lookup_from_slice,
    resolve_cell_transport_kind,
)


def test_lookup_maps_registry_transport_kind_to_domain_kind() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    lk = transport_kind_lookup_from_slice(sl)
    assert lk["space_belt"] is TransportKind.SHAPE_BELT


def test_resolve_cell_prefers_domain_enum_over_registry() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("shape_belt", "belt", "bv:1"),),
        (),
    )
    assert (
        resolve_cell_transport_kind("shape_belt", catalog_slice=sl)
        is TransportKind.SHAPE_BELT
    )


def test_resolve_cell_uses_registry_key_when_not_domain_enum() -> None:
    sl = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    assert (
        resolve_cell_transport_kind("space_belt", catalog_slice=sl)
        is TransportKind.SHAPE_BELT
    )


def test_resolve_cell_without_catalog_returns_none_for_unknown() -> None:
    assert resolve_cell_transport_kind("space_belt", catalog_slice=None) is None


def test_resolve_cell_with_catalog_raises_when_unresolved() -> None:
    sl = BuildingCatalogSlice(SLICE_VERSION, (), ())
    with pytest.raises(CatalogTransportUnresolvedError):
        resolve_cell_transport_kind("unknown_wire", catalog_slice=sl)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py -v
```

Expected: FAIL — `transport_kind_lookup_from_slice` / `resolve_cell_transport_kind` not defined.

- [ ] **Step 3: Implement minimal policy**

In `catalog_transport_policy.py`, keep existing T1 exports; add:

```python
def transport_kind_lookup_from_slice(
    catalog_slice: BuildingCatalogSlice,
) -> dict[str, TransportKind]:
    """Map game-data registry ``transport_kind`` keys to domain ``TransportKind``."""

    lookup: dict[str, TransportKind] = {}
    for entry in catalog_slice.transport_registry:
        category = entry.transport_category.strip().lower()
        kind = _TRANSPORT_CATEGORY_TO_KIND.get(category)
        if kind is None:
            continue
        lookup[entry.transport_kind] = kind
    return lookup


def resolve_cell_transport_kind(
    raw: str,
    *,
    catalog_slice: BuildingCatalogSlice | None,
    lookup: dict[str, TransportKind] | None = None,
) -> TransportKind | None:
    """Resolve one cell wire string; RTTP callers pass ``catalog_slice`` and fail via adapter."""

    for member in TransportKind:
        if member.value == raw:
            return member
    if catalog_slice is None:
        return None
    table = lookup if lookup is not None else transport_kind_lookup_from_slice(catalog_slice)
    mapped = table.get(raw)
    if mapped is not None:
        return mapped
    raise CatalogTransportUnresolvedError(
        CatalogTransportErrorCode.CATALOG_TRANSPORT_UNRESOLVED,
        f"cannot resolve transport_kind wire {raw!r} from catalog registry",
    )
```

Update `__all__` with the two new symbols.

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py -v
```

Expected: PASS (all tests in file).

- [ ] **Step 5: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/adapters/catalog_transport_policy.py tests/unit/asteroid_lab/test_catalog_transport_policy.py
```

Expected: no issues.

---

### Task 2: Wire T2 into `reconstruction_adapter`

**Files:**
- Modify: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py`
- Test: `tests/unit/asteroid_lab/test_optimization_input_adapter.py`

- [ ] **Step 1: Write failing adapter tests**

Add helpers and tests to `test_optimization_input_adapter.py`:

```python
def _pipe_cell_registry_key(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="SpacePipe_Forward",
        cell_kind="space_pipe",
        transport_kind="space_pipe",  # registry key, not domain enum
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "SpacePipe_Forward"},
    )


def test_existing_transport_resolves_registry_key_via_catalog_slice() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell_registry_key(4, 5),)
    catalog_slice = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_pipe", "pipe", "bv:1"),),
        (),
    )
    inp = optimization_input_from_reconstruction(
        ReconstructionResult(cells=cells),
        catalog_slice=catalog_slice,
    )
    assert inp.existing_transport_cells == frozenset(
        {ExistingTransportCell(coord=(4, 5), transport_kind=TransportKind.FLUID_PIPE)}
    )


def test_unresolved_transport_cell_fails_when_catalog_slice_present() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell_registry_key(4, 5),)
    catalog_slice = BuildingCatalogSlice(SLICE_VERSION, (), ())
    with pytest.raises(CatalogTransportUnresolvedError):
        optimization_input_from_reconstruction(
            ReconstructionResult(cells=cells),
            catalog_slice=catalog_slice,
        )
```

Add imports: `pytest`, `CatalogTransportUnresolvedError`, `ExistingTransportCell`, `TransportKind.FLUID_PIPE`.

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/unit/asteroid_lab/test_optimization_input_adapter.py::test_existing_transport_resolves_registry_key_via_catalog_slice tests/unit/asteroid_lab/test_optimization_input_adapter.py::test_unresolved_transport_cell_fails_when_catalog_slice_present -v
```

Expected: FAIL — pipe cell skipped or no exception.

- [ ] **Step 3: Implement adapter wiring**

In `reconstruction_adapter.py`:

1. Import `resolve_cell_transport_kind`, `transport_kind_lookup_from_slice` from `catalog_transport_policy`.
2. Change `_existing_transport` signature to accept optional `catalog_slice` and prebuilt lookup:

```python
def _existing_transport(
    by_coord: dict[Coord, DecodedCellDTO],
    *,
    catalog_slice: BuildingCatalogSlice | None = None,
) -> frozenset[ExistingTransportCell]:
    lookup = (
        transport_kind_lookup_from_slice(catalog_slice)
        if catalog_slice is not None
        else None
    )
    transport: list[ExistingTransportCell] = []
    for coord, cell in by_coord.items():
        if not _is_reconstruction_transport_cell(cell):
            continue
        if catalog_slice is not None:
            kind = resolve_cell_transport_kind(
                cell.transport_kind,
                catalog_slice=catalog_slice,
                lookup=lookup,
            )
        else:
            kind = _parse_transport_kind(cell.transport_kind)
            if kind is None:
                continue
        transport.append(ExistingTransportCell(coord=coord, transport_kind=kind))
    return frozenset(transport)
```

3. In `optimization_input_from_reconstruction`, call:

```python
existing_transport = _existing_transport(by_coord, catalog_slice=catalog_slice)
```

4. Remove unused `_parse_transport_kind` only if no callers remain; otherwise keep for legacy branch.

- [ ] **Step 4: Run adapter + policy tests**

```bash
python -m pytest tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_optimization_input_adapter.py -v
```

Expected: PASS.

- [ ] **Step 5: Reconstruction narrow gate (unchanged behavior)**

```powershell
powershell -File scripts/test_reconstruction_narrow.ps1
```

Expected: PASS (no reconstruction module edits).

- [ ] **Step 6: Ruff**

```bash
python -m ruff check django_apps/asteroid_lab/adapters/catalog_transport_policy.py django_apps/asteroid_lab/optimization/reconstruction_adapter.py tests/unit/asteroid_lab/test_catalog_transport_policy.py tests/unit/asteroid_lab/test_optimization_input_adapter.py
```

---

### Task 3: Domain doc + parent spec cross-link

**Files:**
- Modify: `docs/domain/asteroid_game_data_snapshot.md`
- Modify: `docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md` (short T2 subsection only)

- [ ] **Step 1: Add T2 under B2 slice section in domain doc**

After the T1 sentence, add:

```markdown
**T2 (RTTP):** Per transport cell, `resolve_cell_transport_kind` maps reconstruction `transport_kind` wire strings through `transport_registry` (`transport_kind` key → `transport_category` → `TransportKind`). Domain enum values (`shape_belt`, `fluid_pipe`) pass through. Unresolved transport tiles with a catalog slice fail closed (`catalog_transport_unresolved`).
```

- [ ] **Step 2: Replace design spec non-goal line with T2 summary**

In `2026-05-24-building-catalog-slice-first-consumption-design.md`, move T2 from Non-goals to a new `## T2 — resolve_cell_transport_kind` section (5–10 lines) pointing to this plan. Keep non-goals list for T3+.

- [ ] **Step 3: No pytest required for docs-only** (skip unless doc task accidentally touches code).

---

### Task 4: PR narrow verification (agent closing)

- [ ] **Step 1: Architecture boundary unchanged**

```bash
python -m pytest tests/unit/architecture/test_catalog_consumption_boundaries.py -v
```

Expected: PASS.

- [ ] **Step 2: Optional entry smoke (if fixture exists)**

If `tests/unit/asteroid_lab/test_solver_runtime_entry.py` has catalog transport cases, run:

```bash
python -m pytest tests/unit/asteroid_lab/test_solver_runtime_entry.py -k catalog -v
```

Do **not** add macro E2E or new solver integration tests in this PR unless a minimal unit test is needed; entry already maps `CatalogTransportUnresolvedError`.

- [ ] **Step 3: Full gate only when user requests PR close**

Per [`AGENTS.md`](../../../AGENTS.md): `powershell -File scripts/test_full.ps1` → `ruff check .` → `mypy django_apps config src` → `black --check .`

---

## Plan self-review (completed at write time)

| Check | Result |
|-------|--------|
| Spec coverage (T2 per-cell via registry) | Tasks 1–2 |
| Placeholder scan | No TBD steps |
| Type/name consistency | `resolve_cell_transport_kind`, `transport_kind_lookup_from_slice` used throughout |
| Forbidden scope | Out of scope table + no forbidden file paths in tasks |
| Narrow PR | 2 code modules + 2 test modules + docs |

---

## Execution handoff

**Plan saved to:** `docs/superpowers/plans/2026-05-24-b2-t2-per-cell-transport-resolution.md`

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — same session with executing-plans, checkpoint after Task 2

Which approach do you want?
