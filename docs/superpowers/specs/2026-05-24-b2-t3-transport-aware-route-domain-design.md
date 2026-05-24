# B2-T3 — Transport-Aware Route Domain

**Status:** Approved 2026-05-24 (Policy B + Approach 1; INV-B2T3-08 ring/trunk overlap)  
**Predecessor:** B2-T2 per-cell transport resolution (PR #60, merged)  
**Parent track:** [Building Catalog Slice First Consumption](2026-05-24-building-catalog-slice-first-consumption-design.md)  
**Implementation plan:** [`2026-05-24-b2-t3-transport-aware-route-domain.md`](../plans/2026-05-24-b2-t3-transport-aware-route-domain.md) (written after this spec)

> **Naming:** This **B2-T3** transport-domain slice is distinct from the catalog **Track D / geometry T3** discussed in the parent B2 design (footprint, connector, candidate validation from catalog).

## Problem

B2-T2 resolves each reconstruction transport cell’s `transport_kind` (`shape_belt`, `fluid_pipe`, registry keys). RTTP still seeds skeleton `trunk_mask_cells` from **all** `existing_transport_cells` regardless of `OptimizationInput.transport_kind`, and route-domain construction does not hard-block incompatible cells. That allows:

- Shape-belt routes to use `fluid_pipe` coords as trunk/seed or walkable corridor.
- Fluid-pipe routes to use `shape_belt` coords the same way.
- Candidate/commit probes to treat wrong-kind existing transport as viable path.

Wrong-kind existing transport is treated as incompatible occupied transport: it is excluded from trunk/seed/goal sets and inserted into route-domain blocked cells.

## Success criterion

```text
RTTP route/probe/commit respects TransportKind on existing_transport_cells.
Same-kind cells may seed trunk; wrong-kind cells are hard-blocked in RouteCellDomain.
Diagnostics expose mismatch counts without becoming solver input.
Greenfield shape_belt smoke, reconstruction narrow gate, and RTTP narrow tests stay green.
```

## Non-goals (this slice)

| Area | Reason |
|------|--------|
| Full `RouteDomainSnapshotBuilder` module | Deferred; extend `build_route_domain_from_skeleton` only |
| Macro compiler / MacroBundle T3 | Macro track PAUSED |
| Selection, fitness, regret | Forbidden |
| Validation relax / new bypass | Forbidden |
| LNS algorithm changes | Out of scope |
| Replay frames as solver input | Forbidden |
| Footprint / connector / catalog geometry (Track D) | Separate track |
| Dual `transport_kind` runs in one pipeline pass | Single `inp.transport_kind` per run (unchanged) |
| Per-cell registry resolution (T2) | Closed in B2-T2; B2-T3 consumes resolved `ExistingTransportCell` |

## Policy B — normative contract

For RTTP route-domain construction, existing transport cells whose `transport_kind` differs from `OptimizationInput.transport_kind` are excluded from trunk/seed/goal sets and inserted into the route-domain blocked set. They remain available only for diagnostics via the full `existing_transport_cells` set.

| ID | Rule |
|----|------|
| INV-B2T3-01 | `existing_transport_cells` retains every T2-resolved transport cell (no filtering). |
| INV-B2T3-02 | `existing_trunk_cells` ⊆ coords where `cell.transport_kind == inp.transport_kind`. |
| INV-B2T3-03 | `blocked_incompatible_transport_cells` = coords where `cell.transport_kind != inp.transport_kind`. |
| INV-B2T3-04 | ∀ c ∈ `blocked_incompatible_transport_cells`: coord ∉ skeleton trunk seed used for active kind; coord ∈ `RouteCellDomain.blocked_cells`. |
| INV-B2T3-05 | Blocked union order: compute base blocked from mineable/void minus platform/trunk/lift/goals, **then** union `blocked_incompatible_transport_cells`. |
| INV-B2T3-06 | `probe_goal_coords` continues to filter `route_goals` by `inp.transport_kind`; no wrong-kind margin goals. |
| INV-B2T3-07 | Diagnostics metrics are output-only; never read by solver algorithms. |
| INV-B2T3-08 | `blocked_incompatible_transport_cells` are removed from any `trunk_mask` / traversable seed set before `RouteCellDomain` is finalized, **even if they overlap `ring_cells`**. A coord MUST NOT be both trunk/traversable and incompatible-blocked. |

Semantic: wrong-kind existing transport = **incompatible occupied transport** → hard no-go for route probe and commit reprobe (same class as other `blocked_cells`).

## Architecture (Approach 1)

```text
reconstruction_adapter
  partition_existing_transport(existing, active_kind)
    → existing_transport_cells (full)
    → existing_trunk_cells (same-kind coords)
    → blocked_incompatible_transport_cells (wrong-kind coords)
    → mismatched_existing_transport_by_kind (metrics helper)

RttpSkeletonBuilder
  trunk_mask = (ring_cells | existing_trunk_cells) - blocked_incompatible_transport_cells

build_route_domain_from_skeleton
  trunk_mask = skeleton.trunk_mask_cells - blocked_incompatible_transport_cells  # defense in depth
  blocked = base_blocked - ... ; blocked |= blocked_incompatible_transport_cells  # after trunk/lift/goal subtract
  traversable = trunk_mask | lift | goals   # incompatible never in traversable

incremental_commit._rebuild_domain
  inherits base.blocked_cells (includes incompatible)

pipeline RTTP_ROUTE_DOMAIN step
  metrics: mismatched_existing_transport_count, mismatched_existing_transport_by_kind
```

No new `RouteDomainSnapshotBuilder` type in B2-T3.

## `OptimizationInput` extension

```python
blocked_incompatible_transport_cells: frozenset[Coord] = frozenset()
```

- **Implementation field:** `blocked_incompatible_transport_cells` (domain semantics).
- **Output metrics:** `mismatched_existing_transport_count`, `mismatched_existing_transport_by_kind` (observability only).
- Default empty frozenset for greenfield fixtures and manual test `OptimizationInput` builders.

## Partition API (adapter-owned)

Location: `django_apps/asteroid_lab/optimization/reconstruction_adapter.py` (pure functions, no new cross-layer imports).

```python
def partition_existing_transport(
    existing_transport: frozenset[ExistingTransportCell],
    active_kind: TransportKind,
) -> tuple[
    frozenset[Coord],  # same_kind_trunk_coords
    frozenset[Coord],  # blocked_incompatible_coords
    dict[str, int],    # mismatched_existing_transport_by_kind
]:
    ...
```

`mismatched_existing_transport_count` = `len(blocked_incompatible_coords)`.

`mismatched_existing_transport_by_kind` keys use `TransportKind.value` (`"shape_belt"`, `"fluid_pipe"`).

## Skeleton (`skeleton_builder.py`)

When merging ring spine with existing trunk:

```python
trunk_mask_cells = frozenset(
    (option.ring_cells | inp.existing_trunk_cells) - inp.blocked_incompatible_transport_cells
)
```

## Route domain (`lift_lane_domain.py`)

In `build_route_domain_from_skeleton`:

1. `incompatible = inp.blocked_incompatible_transport_cells`
2. `trunk_mask = frozenset(skeleton.trunk_mask_cells - incompatible)` (INV-B2T3-08; idempotent if skeleton already subtracted).
3. Build `lift_coords`, `goal_coords` as today.
4. `blocked = (mineable | external_void) - platform - trunk_mask - lift - goals`.
5. `blocked = blocked | incompatible` (union **after** subtract so incompatible coords stay blocked even if they were wrongly present on ring).
6. `traversable_cells = (trunk_mask | lift_coords | goal_coords) - incompatible` — incompatible coords MUST NOT appear in traversable (including when a coord overlaps `lift_coords`).

`incremental_commit._rebuild_domain` unchanged except it automatically preserves incompatible blocks via `base.blocked_cells`.

## Diagnostics

Emit on **`RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN`** (`rttp.route_domain`) pipeline step `metrics` / `metrics_json`:

| Key | Type |
|-----|------|
| `mismatched_existing_transport_count` | int |
| `mismatched_existing_transport_by_kind` | `dict[str, int]` |

Optional replay overlay for incompatible cells: **YAGNI** unless a test requires it.

## Tests (minimum)

| Test | File |
|------|------|
| `test_route_probe_ignores_mismatched_existing_transport_kind` | `tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py` |
| `test_shape_route_does_not_use_fluid_pipe_trunk_seed` | same |
| `test_fluid_route_does_not_use_shape_belt_trunk_seed` | same |
| `test_transport_kind_mismatch_diagnostics` | same |
| `test_incompatible_on_ring_excluded_from_trunk_not_traversable` | same (INV-B2T3-08) |

Regression updates:

- `test_rttp_existing_trunk.py` — same-kind trunk only.
- `test_optimization_input_adapter.py` — mixed belt+pipe fixture asserts partition fields.

## Verification gate

```powershell
python -m pytest tests/unit/asteroid_lab -k "transport_kind or route_probe or rttp" -v
powershell -File scripts/test_reconstruction_narrow.ps1
python -m ruff check django_apps/asteroid_lab/optimization django_apps/asteroid_lab/adapters tests/unit/asteroid_lab
```

PR branch: `feature/b2-t3-transport-aware-route-domain` from **post–B2-T2** `master`.

## Spec self-review (2026-05-24, rev 2)

| Check | Result |
|-------|--------|
| Required Policy B sentence | Present in Problem + Policy B |
| Track D naming disambiguation | Present in header |
| Field vs metrics naming split | Documented |
| Union order invariant | INV-B2T3-05 |
| Ring/trunk overlap (no dual membership) | INV-B2T3-08 + skeleton + domain sections |
| Placeholder scan | No TBD |
| Scope vs parent B2 geometry T3 | Non-goals + naming note |
