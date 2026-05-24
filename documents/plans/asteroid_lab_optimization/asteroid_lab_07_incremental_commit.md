---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: pre-RTTP plan snapshot; see documents/Algorithm/ and docs/superpowers/specs/
superseded_by:
  - documents/ai/current_plan.md
  - docs/superpowers/specs/2026-05-22-rttp-hybrid-c-layout-design.md
---

# Phase 7 — Incremental Route Commit


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Confirm the best genome selected by evolutionary search as actual layout candidates.

## Core principle

```text
Everything is provisional until connected to exterior trunk.
```

## Flow

```text
best genome
→ candidate commit_order sequence
→ re-run route probe (commit-time domain·reservation reflected)
→ reserve path
→ detect conflict
→ commit route + **full route_domain rebuild (RouteDomainSnapshotBuilder)**
→ promote placement
→ rollback failed candidate
```

## Incremental commit behavior (`commit_best_genome`)

```text
1) Immediately before each candidate, create fresh route_domain via
   `RouteDomainSnapshotBuilder.build_snapshot(...)` (confirmed_reservations·committed_occupied_cells reflected).
2) `BundleCandidate.route_probe_result` from candidate generation is reference only;
   not final proof in commit loop.
3) Each commit candidate always re-runs `run_route_probe` with **latest route_domain at that moment**.
4) On commit success, reserved path promotes to trunk·preferred for same `transport_kind`;
   other kinds blocked·limited via `transport_mask` etc. (`RouteDomainSnapshotBuilder.build_snapshot` overlay).
5) `occupied_cells` of confirmed placement become `hard_blocked` in subsequent snapshots.
```

Commit code does **not in-place patch** `RouteCellDomain`. Snapshot is new `dict[Coord, RouteCellDomain]` from builder.

## commit_order source (prevent greedy order leak)

Actual confirmation order authority is **selected genome's `Gene.commit_order` only**. Must **not** use as default commit order:

```text
rim scan order
candidate generation·enumeration order
coord lex order (sole authority)
```

Use above only as **tie-break** in documented exceptions; otherwise follow `commit_order` explicit in genome. Otherwise candidate generation order leaks as de facto **greedy install order**.

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
ROUTED -> CONFIRMED: reservation·**route_domain snapshot**·occupancy map atomically reflected (implementation: single transaction or equivalent rollback unit)
FEASIBLE -> ROLLED_BACK: re-probe failure or preliminary validation failure
ROUTED -> ROLLED_BACK: reservation conflict·policy violation aborts commit
CONFIRMED -> ROLLED_BACK: forbidden in v0 (only full transaction abort allowed)
```

If requirement emerges to rollback single candidate after `CONFIRMED`, open separate transaction model in v1 plan.

## Recovery budget (thrashing cap)

corridor carve·rollback·re-probe loops can become **infinite**. v0 defines **cap DTO** below; on exceed terminate with `CommitConflictReason`·`ROLLED_BACK` etc. (values may separate from `EvolutionConfig`).

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

## Route domain transition (replay·debug minimal contract)

`frozenset[Coord]` alone makes **why blocked/preferred changed** hard to recover. Each reservation leaves **minimal before/after** for applied cells.

```python
@dataclass(frozen=True)
class RouteDomainCellTransition:
    coord: Coord
    route_class_before: RouteClass
    route_class_after: RouteClass
```

`RouteClass` uses same enum·meaning as Phase 4 `RouteCellDomain.route_class`. Need not include all hard_blocked·mask·cost changes; **v0 must not truncate below two fields** in serialization.

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

- `reservation_id`: **same string** as Phase 8 `ValidationIssue.route_reservation_id`. **UUID forbidden.** v0 authority example: `f"{candidate_id}:route:{ordinal}"` — `ordinal` is **0-based increasing int** within one incremental commit pass (deterministic).
- `reached_goal` / `goal_priority`: needed for trunk·margin·attachment distinction·validation·replay (copy consistent with Phase 4 `RouteProbeResult`).
- `domain_cell_transitions`: record only `RouteCellDomain.route_class` **changed** by this commit (omit unchanged coords). Even if builder full-rebuilds, **debug·replay must restore “what changed” from this tuple**.
- `reservation_state`: provisional vs confirmed distinction at commit stage.

**Deprecated:** form with only `reserved_domain_delta: frozenset[Coord]` lacks debug utility; **excluded from authority** in this doc.

## Post-commit `route_domain`·trunk update contract (P0)

When commit **succeeds (CONFIRMED)**:

```text
1) For that transport_kind, reserved path cells are treated as trunk·preferred region
   or policy-allowed passage in later candidate probes for same kind.
2) For other transport_kind candidates, same cells may reflect blocked·high cost·mask mismatch.
3) Next candidate RouteProbeInput.route_domain is rebuilt reflecting
   CONFIRMED reservations + placement occupied so far.
```

Without this contract, candidate-phase “reachable” and final commit conflict **separate again**. Phase 3 immediate probe is **snapshot at that time**; commit loop **always re-probes with latest domain**.

## RouteDomainSnapshotBuilder — route_domain snapshot authority API

Same as Algorithm authority — see [`asteroid_lab_07_incremental_commit.md`](../../Algorithm/asteroid_lab_07_incremental_commit.md) §RouteDomainSnapshotBuilder API table. Summary: `build_snapshot` authority; `build_commit_snapshot` optional deprecated wrapper (no separate semantics); implementation `commit_selected_candidates`.

## `blocked_cells` vs `protected_corridor_cells` (semantic separation)

- **`blocked_cells`** (`OptimizationInput`): general **hard no-go** cell set.  
  - Path crossing `blocked_cells` in commit path check (`incremental_commit._path_conflict_reason`) → **`CommitConflictReason.HARD_BLOCKED_CONFLICT`** (`"hard_blocked_conflict"`).
- **`protected_corridor_cells`**: protected·policy-sensitive **corridor** cells.  
  - Reject commit for **policy violation** → **`HARD_PROTECTED_CONFLICT`** (`"hard_protected_conflict"`) (distinct from general hard no-go).  
  - Allowing corridor as **permitted passage** via cost·mask is `RouteDomainSnapshotBuilder` / `RouteCellDomain` policy (seed·overlay) responsibility; not same treatment as `blocked_cells`.

## Conflict

Conflict reasons 1:1 with **`CommitConflictReason` StrEnum** (free strings forbidden).

```python
from enum import StrEnum


class CommitConflictReason(StrEnum):
    OCCUPIED_CELL_CONFLICT = "occupied_cell_conflict"
    ROUTE_CELL_CONFLICT = "route_cell_conflict"
    TRANSPORT_KIND_CONFLICT = "transport_kind_conflict"
    HARD_BLOCKED_CONFLICT = "hard_blocked_conflict"
    HARD_PROTECTED_CONFLICT = "hard_protected_conflict"
    TRUNK_DEADLOCK = "trunk_deadlock"
    ROUTE_PROBE_FAILED = "route_probe_failed"
```

Doc·test code strings match member names.

## Rollback

On commit failure, rollback that candidate only.

Do not touch other confirmed candidates.

## Invariant

```text
[ ] confirmed placement must have connected route (re-probe success snapshot)
[ ] failed commit must not mutate confirmed routes
[ ] shape belt and fluid pipe reservations are separated
[ ] route reservation does not occupy extractor/extension cells
[ ] rollback is local and reversible
[ ] RouteReservation.reservation_id created per same rule as Phase 8 route_reservation_id
[ ] route_domain rebuild after CONFIRMED reflected in subsequent probe input
[ ] commit attempt order authority is selected genome `Gene.commit_order` (not rim scan·candidate generation order as default)
[ ] reserved_cells set synchronized with path without contradiction (cross Phase 8 Validation)
[ ] each domain_cell_transitions element consistent with RouteClass contract (empty tuple may mean “no route_class change”)
[ ] RecoveryBudget exceed prevents infinite thrashing
[ ] blocked_cells path cross → HARD_BLOCKED_CONFLICT; protected corridor **policy violation** → HARD_PROTECTED_CONFLICT (no semantic confusion)
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
- **`build_snapshot` single entry**: `commit_selected_candidates` → `build_snapshot` only. `test_incremental_commit_reprobes_latest_domain` etc. — see Algorithm authority.

This doc scope is Sequence 6 incremental commit contract sync; **does not add** Sequence 7 validation (`ValidationIssueCode` etc.) implementation·UI·CP-SAT·replay·recovery logic.

## Completion criteria

```text
[ ] best genome commit pipeline implemented
[ ] RouteReservation (reservation_id·reached_goal·goal_priority·state·domain_cell_transitions) implemented
[ ] RecoveryBudget contract and exceed termination path
[ ] CommitConflictReason StrEnum (`HARD_BLOCKED_CONFLICT`·`HARD_PROTECTED_CONFLICT` etc.)
[ ] post-commit route_domain update contract implemented·tested
[ ] commit attempt order authority genome `Gene.commit_order` (not generation·rim order default)
[ ] local rollback implemented
[ ] confirmed route invariant tests pass
```
