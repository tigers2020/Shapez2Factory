---
status: CANCELLED
cancelled_date: 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---
# Shared Transport Inlet ??Design Spec (Solver Runtime v0)

**Status:** Approved 2026-05-22  
**Owner:** solver-runtime-pipeline  
**Related:** [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md), [`phase_i_candidate_selection.md`](../../../documents/Algorithm/solver_runtime/phase_i_candidate_selection.md), [`00_core_principles.md`](../../../documents/Algorithm/solver_runtime/00_core_principles.md)

## Problem

Rim packing places many `GeneTemplate` bundles (from DB `GeneticSample`). Users observed:

- **Extractor + extensions** cannot overlap (mineable `occupied_cells`).
- **Belt/pipe route cells** may be **shared** across bundles (same `TransportKind`).
- **Worst placement:** a third miner places its **outlet on an existing shared trunk cell**, blocking inward access for miners on both sides.

The solver must treat route sharing and inlet blocking as **different layers**, not one blanket `equipment_transport_overlap`.

## Approved v0 rules (user YES 2026-05-22)

| Layer | Rule |
|-------|------|
| **Equipment footprint** | `occupied_cells` pairwise disjoint across selected/committed bundles (**unchanged**). |
| **Route sharing** | Same-kind **route path / reserved cells** may overlap across bundles (**explicitly allowed**). |
| **Inlet on shared transport** | **Forbidden:** `candidate.fixed_output_transport ??committed_route_cells` (union of cells on confirmed reservation paths / `reserved_cells`). |

### Definitions

- `fixed_output_transport`: canonical first belt/pipe cell after extractor ([`phase_d_gene_templates.md`](../../../documents/Algorithm/solver_runtime/phase_d_gene_templates.md)).
- `committed_route_cells`: all coords on confirmed `RouteReservation.path` (or `reserved_cells`; must be consistent with commit snapshot).
- `occupied_cells`: extractor + extensions only (stub not in footprint dedupe/selection; stub governed by inlet rule).

### Game intuition mapping

```text
OK:   Miner L and Miner R ??routes merge on shared belt/pipe cells downstream
BAD:  Miner C sets fixed_output_transport on a cell already used as transport
      ??blocks ?œinward??injection for existing feeders (ìµœì•…????
```

## Current code gap

- [`commit_best_candidates.py`](../../../django_apps/asteroid_lab/optimization/commit_best_candidates.py) `_equipment_transport_overlap` rejects broad `equipment & committed_route_cells`, which conflates inlet blocking with other touches.
- [`phase_j_incremental_commit.md`](../../../documents/Algorithm/solver_runtime/phase_j_incremental_commit.md) Route sharing bullet ?œsame cell sharing ê¸ˆì???**contradicts** this spec ??**update doc** to match v0.
- Phase I footprint filter does not yet apply inlet rule against **accumulated route cells** (only `occupied_cells`).

## Target behavior

### Phase I ??selection (recommended in same PR)

When greedy-selecting, exclude candidate `c` if:

```text
c.fixed_output_transport ??selected_route_cells
```

where `selected_route_cells` is the union of **planned** route cells for already-ordered candidates. v0 pragmatic source: use each candidate?™s **candidate-phase** `route_probe_result.path` ??`reserved_cells` proxy (document exact field in implementation plan). If proxy unavailable at selection time, **commit-only** enforcement is minimum; selection mirror is preferred to reduce commit skips.

### Phase J ??commit (required)

Before confirming placement, after reprobe path is known:

```text
if candidate.fixed_output_transport in committed_route_cells:
    skip with CommitConflictReason.INLET_ON_SHARED_TRANSPORT
```

Do **not** skip solely because route paths overlap same coords (same kind).

Narrow or replace checks that reject all `equipment & committed_route_cells`; only **`fixed_output_transport`** on transport cells is forbidden for v0.

### Phase K / K2 ??materialization (implemented 2026-05-22)

[`merge_materialized_layout`](../../../django_apps/asteroid_lab/optimization/placement_network_materializer.py): on coord overlap, **transport wins** ??equipment on shared trunk coords is dropped; hard fail only if overlap remains after drop. Test: `test_merge_transport_wins_on_shared_trunk_coord_overlap`.

[`validate_final_layout`](../../../django_apps/asteroid_lab/optimization/final_validation.py): extension at a transport coord counts as materialized (no `placement_not_materialized`). Test: `test_validation_accepts_extension_on_shared_transport_coord`.

## Contract changes

### `CommitConflictReason` (StrEnum ??no free strings)

Add:

```python
INLET_ON_SHARED_TRANSPORT = "inlet_on_shared_transport"
```

Deprecate or narrow semantics of `EQUIPMENT_TRANSPORT_OVERLAP` in docs/tests: v0 commit tests should assert `INLET_ON_SHARED_TRANSPORT` for stub-on-trunk case.

### `solver_summary` / replay

- `commit_inlet_on_shared_transport_count` (or bucket under `skipped_by_reason`)
- Optional: `selection_skipped_inlet_on_shared_transport_count`

## Testing (implemented 2026-05-22)

| Test | Behavior | Status |
|------|----------|--------|
| `test_commit_rejects_fixed_output_transport_on_committed_route_cell` | stub on committed transport cell ??`INLET_ON_SHARED_TRANSPORT` | done |
| `test_commit_allows_same_kind_route_path_sharing_after_stub` | `path[1:]` shares trunk; distinct stubs ??both confirmed | done |
| `test_selector_skips_stub_on_accumulated_transport_cells` | Phase I mirror | done ([`2026-05-22-phase-i-commit-survivability-design.md`](2026-05-22-phase-i-commit-survivability-design.md)) |
| Regression | `test_incremental_commit.py` full module | green |

## Out of scope (v0)

- Rim band / throughput-group spatial packing
- ~~Extension body on shared trunk at commit~~ ??[`2026-05-22-commit-extension-shared-trunk-design.md`](2026-05-22-commit-extension-shared-trunk-design.md)
- Fluid vs shape on same cell (still `TRANSPORT_KIND_CONFLICT`)
- Changing `target_miner_bundle_count` / capacity planner

## Verification

```bash
python -m pytest tests/unit/asteroid_lab/test_incremental_commit.py tests/unit/asteroid_lab/test_candidate_selector.py
python -m ruff check django_apps/asteroid_lab/optimization/commit_best_candidates.py django_apps/asteroid_lab/optimization/candidate_selector.py
```

## Implementation order (for writing-plans)

1. Enum + commit check (narrow `_equipment_transport_overlap` ??inlet-only)
2. Unit tests (sharing allowed vs stub forbidden)
3. Phase I mirror (optional same PR if path proxy clear)
4. Doc sync: `phase_j`, `phase_i`, this spec linked from [`README.md`](../../../documents/Algorithm/solver_runtime/README.md) open decisions if needed
