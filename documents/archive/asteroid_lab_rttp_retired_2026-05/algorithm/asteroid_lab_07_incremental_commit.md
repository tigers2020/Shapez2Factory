# Phase 7 — Incremental Route Commit

## Purpose

Commit the best genome selected by evolutionary search as actual layout candidates.

## Core principle

```text
Everything is provisional until connected to exterior trunk.
```

## Flow

```text
best genome
→ candidate commit_order order
→ re-run route probe (commit-time domain·reservation reflected)
→ reserve path
→ detect conflict
→ commit route + **full route_domain rebuild (RouteDomainSnapshotBuilder)**
→ promote placement (route_domain `committed_occupied_cells` + K2 `equipment_cells` materialization)
→ rollback failed candidate
```

## Incremental commit behavior (`commit_best_genome`)

```text
1) Immediately before each candidate, create route_domain anew with
   `RouteDomainSnapshotBuilder.build_snapshot(...)` (confirmed_reservations·committed_occupied_cells reflected).
2) `BundleCandidate.route_probe_result` from candidate generation is reference only;
   not final proof in commit loop.
3) Each commit candidate always re-runs `run_route_probe` with **latest route_domain at that moment**.
4) On commit success, reserved path promotes to trunk·preferred for same `transport_kind`;
   other kinds blocked·limited via `transport_mask` etc. (`RouteDomainSnapshotBuilder.build_snapshot` overlay).
5) Confirmed placement `occupied_cells` reflected as `hard_blocked` in subsequent snapshots.
```

Commit code does **not** patch `RouteCellDomain` **in-place**. Snapshot builder returns new `dict[Coord, RouteCellDomain]`.

## commit_order source (greedy order leak prevention)

Actual commit order is canonical only in **selected genome's `Gene.commit_order`**. Must **not** use as default commit order:

```text
rim scan order
candidate generation·enumeration order
coord lex order (standalone canonical)
```

Use above only as auxiliary keys in documented tie-break exceptions; otherwise follow `commit_order` explicit in genome. Otherwise candidate generation order effectively **leaks as greedy installation order**.

## States

```python
class PlacementCommitState(Enum):
    PROVISIONAL = "provisional"
    FEASIBLE = "feasible"
    ROUTED = "routed"
    CONFIRMED = "confirmed"
    ROLLED_BACK = "rolled_back"
```

### State transitions (v0)

```text
PROVISIONAL -> FEASIBLE: candidate enters commit attempt queue for evaluation
FEASIBLE -> ROUTED: re-probe success + RouteReservation created
ROUTED -> CONFIRMED: reservation·**route_domain snapshot**·occupancy map applied atomically (implementation: single transaction or equivalent rollback unit)
FEASIBLE -> ROLLED_BACK: re-probe failure or provisional validation failure
ROUTED -> ROLLED_BACK: commit aborted due to reservation conflict·policy violation
CONFIRMED -> ROLLED_BACK: forbidden in v0 (only full transaction abort allowed)
```

If requirement arises to rollback single candidate after `CONFIRMED`, open separate transaction model in v1 plan.

## Recovery budget (thrashing cap)

Corridor carve·rollback·re-probe repetition can lead to **infinite loop**. v0 defines **cap DTO** below; on exceed terminate with `CommitConflictReason`·`ROLLED_BACK` etc. (values may separate from `EvolutionConfig`).

```python
@dataclass(frozen=True)
class RecoveryBudget:
    max_removed_candidates: int
    max_carve_cells: int
    max_reroute_attempts: int
```

## Reservation state

```python
class ReservationState(Enum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    RELEASED = "released"
```

## Route domain transition (replay·debug minimum contract)

`frozenset[Coord]` alone makes it hard to recover **why blocked/preferred changed**. Each reservation retains **minimum before/after** for affected cells.

```python
@dataclass(frozen=True)
class RouteDomainCellTransition:
    coord: Coord
    route_class_before: RouteClass
    route_class_after: RouteClass
```

`RouteClass` uses same enum·semantics as Phase 4 `RouteCellDomain.route_class`. Need not include all hard_blocked·mask·cost changes, but **v0 must serialize at least the two fields above without truncation**.

## Route Reservation

```python
@dataclass(frozen=True)
class RouteReservation:
    reservation_id: str
    candidate_id: str
    transport_kind: TransportKind
    path: tuple[Coord, ...]
    reserved_cells: frozenset[Coord]
    cost: int
    reached_goal: RouteGoal
    goal_priority: int
    reservation_state: ReservationState
    domain_cell_transitions: tuple[RouteDomainCellTransition, ...]
```

- `reservation_id`: **same string** as Phase 8 `ValidationIssue.route_reservation_id`. **UUID forbidden.** v0 canonical example: `f"{candidate_id}:route:{ordinal}"` — `ordinal` is integer **incrementing from 0** within one incremental commit pass (deterministic).
- `reached_goal` / `goal_priority`: needed for trunk·margin·attachment distinction·validation·replay (copy consistent with Phase 4 `RouteProbeResult`).
- `domain_cell_transitions`: record only `RouteCellDomain.route_class` **changed** by this commit (omit coords with no change). Even if builder full-rebuilds, **debug·replay must restore “what changed” from this tuple**.
- `reservation_state`: provisional vs confirmed distinction in commit phase.

**Deprecated:** form with only `reserved_domain_delta: frozenset[Coord]` lacks debug utility; **excluded from canonical** in this doc.

## Post-commit `route_domain`·trunk update contract (P0)

When commit **succeeds (CONFIRMED)**:

```text
1) For that transport_kind, reserved path cells are treated as trunk·preferred region
   or policy-allowed passage in subsequent candidate probes for same kind.
2) For other transport_kind candidates, same cells may reflect as blocked·high cost·mask mismatch.
3) Next candidate RouteProbeInput.route_domain is rebuilt reflecting
   CONFIRMED reservations + placement occupied so far.
```

Without this contract, candidate-phase “reachable” and final commit conflict **separate again**. Phase 3 immediate probe is **snapshot at that time**; inside commit loop **always re-probe with latest domain**.

## RouteDomainSnapshotBuilder — route_domain snapshot canonical API

| API | Role | Notes |
|-----|------|------|
| `build_snapshot(inp, *, confirmed_reservations=(), committed_occupied_cells=frozenset(), provisional_blocked_cells=frozenset())` | **Canonical** — probe·commit overlay | no separate semantics |
| `build_seed_snapshot(inp)` | empty overlay convenience | equivalent to `build_snapshot(..., all overlays empty)` |
| `build_route_domain_for_projected_gene_probe(inp, projected)` | candidate **provisional** only | single allowed wrapper in [route_probe.py](django_apps/asteroid_lab/optimization/route_probe.py) |
| `build_commit_snapshot(...)` | **unimplemented·optional** | if added, 1-line delegate to `build_snapshot` + `@deprecated` only; no commit-only semantics |

- **Implementation entry:** `commit_selected_candidates` ([commit_best_candidates.py](django_apps/asteroid_lab/optimization/commit_best_candidates.py)) — no `commit_best_genome` / `_invoke_build_commit` (legacy doc deprecated).
- Builder composes cell domain as **immutable snapshot**; commit side **receives new map**, does not in-place fix existing `RouteCellDomain` instances.

## `blocked_cells` vs `protected_corridor_cells` (semantic separation)

- **`blocked_cells`** (`OptimizationInput`): general **hard no-go** cell set.  
  - In commit path check (`incremental_commit._path_conflict_reason`), path crossing `blocked_cells` → **`CommitConflictReason.HARD_BLOCKED_CONFLICT`** (`"hard_blocked_conflict"`).
- **`protected_corridor_cells`**: protected·policy-sensitive **corridor** cells.  
  - When rejecting commit for **policy violation**, use **`HARD_PROTECTED_CONFLICT`** (`"hard_protected_conflict"`) (distinct from general hard no-go).  
  - Allowing corridor as **permitted passage**·cost·mask control is responsibility of `RouteDomainSnapshotBuilder` / `RouteCellDomain` policy (seed·overlay); not same treatment as `blocked_cells`.

## Conflict

Conflict reasons map 1:1 to **`CommitConflictReason` StrEnum** (no free strings).

```python
from enum import StrEnum


class CommitConflictReason(StrEnum):
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    FIXED_OUTPUT_TRANSPORT_CONFLICT = "fixed_output_transport_conflict"  # PR1.5 cross-commit FOT
    HARD_BLOCKED_CONFLICT = "hard_blocked_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    TRUNK_DEADLOCK = "trunk_deadlock"
    ROUTE_PROBE_FAILED = "route_probe_failed"
```

Doc·test code strings stay identical to member names.

**PR1.5 (cross-commit FOT):** `FIXED_OUTPUT_TRANSPORT_CONFLICT` — later `occupied_cells` ∩ prior `committed_fixed_output_transport_cells`, or later FOT ∈ prior `committed_occupied`. Distinct from candidate-generation `FIXED_OUTPUT_TRANSPORT_IN_OCCUPIED`. `CommitDomainState` adds **`committed_fixed_output_transport_cells`** (append-only field; **not** merged into `committed_route_cells` / `reserved_route_cells`).

## Rollback

When candidate commit fails, rollback that candidate only.

Do not touch other confirmed candidates.

## Invariant

```text
[ ] confirmed placement must have connected route (re-probe success snapshot)
[ ] failed commit must not mutate confirmed routes
[ ] shape belt and fluid pipe reservations are separated
[ ] route reservation does not occupy extractor/extension cells
[ ] rollback is local and reversible
[ ] RouteReservation.reservation_id generated with same rule as Phase 8 route_reservation_id
[ ] post-CONFIRMED route_domain rebuild reflected in subsequent probe input
[ ] commit attempt order is canonical from selected genome `Gene.commit_order` (not rim scan·candidate generation order as default)
[ ] reserved_cells set synchronized with path without contradiction (Phase 8 Validation cross-ref)
[ ] each domain_cell_transitions element consistent with RouteClass contract (empty tuple may mean “no route_class change”)
[ ] RecoveryBudget exceed prevents infinite thrashing
[ ] path crossing `blocked_cells` is `HARD_BLOCKED_CONFLICT`; protected corridor **policy violation** is `HARD_PROTECTED_CONFLICT` (no semantic confusion)
[ ] PR1.5: confirmed extractor FOT cells reserved in `committed_fixed_output_transport_cells`; no later extractor on peer FOT
[ ] PR1.5: FOT reservation ≠ route reservation (do not add FOT to `reserved_route_cells`)
```

## Tests

`tests/unit/asteroid_lab/test_incremental_commit.py`:

```text
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_does_not_mutate_existing_confirmed_routes
test_incremental_commit_transport_kind_conflict
test_incremental_commit_route_reservation_excludes_occupied_cells
test_incremental_commit_route_domain_reflects_prior_reservations
test_incremental_commit_reservation_id_deterministic
test_incremental_commit_uses_gene_commit_order_not_candidate_id
test_incremental_commit_reprobes_latest_route_domain
test_incremental_commit_failed_candidate_does_not_remove_prior_confirmed
test_incremental_commit_reserved_cells_match_path
test_incremental_commit_domain_cell_transitions_serialized
test_incremental_commit_conflict_reason_enum_only
test_incremental_commit_shape_and_fluid_domains_separated
test_incremental_commit_confirmed_occupied_cells_become_hard_blocked
test_incremental_commit_recovery_budget_exceeded
test_incremental_commit_route_cell_conflict
test_incremental_commit_hard_blocked_conflict
test_incremental_commit_occupied_cell_conflict_on_path
```

- **`HARD_BLOCKED_CONFLICT`**: `test_incremental_commit_hard_blocked_conflict`
- **`build_snapshot` single entry**: `commit_selected_candidates` calls only `RouteDomainSnapshotBuilder.build_snapshot`. Equivalent verification: `test_incremental_commit_reprobes_latest_domain`(new `route_domain` object per probe)·`test_incremental_commit_confirmed_occupied_cells_become_hard_blocked`(overlay snapshot).

This doc scope is Sequence 6 incremental commit contract sync; **does not add Sequence 7 validation (`ValidationIssueCode` etc.) implementation·UI·CP-SAT·replay·recovery logic.**

## Completion criteria

```text
[ ] best genome commit pipeline implementation
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions) implementation
[ ] RecoveryBudget contract and exceed termination path
[ ] CommitConflictReason StrEnum (`HARD_BLOCKED_CONFLICT`·`HARD_PROTECTED_CONFLICT` etc.)
[ ] post-commit route_domain update contract implementation·tests
[ ] commit attempt order canonical from genome `Gene.commit_order` (not generation·rim order default)
[ ] local rollback implementation
[ ] confirmed route invariant tests pass
```
