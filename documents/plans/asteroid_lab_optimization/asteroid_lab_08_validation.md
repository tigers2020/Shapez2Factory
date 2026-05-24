---
status: ARCHIVED
do_not_use_as_authority: true
archived_reason: plans/asteroid_lab_optimization snapshot — use documents/Algorithm/asteroid_lab_08_validation.md
authority_for_implementation: documents/Algorithm/asteroid_lab_08_validation.md
superseded_by:
  - documents/index/document_inventory.md
  - documents/ai/current_plan.md
last_reviewed: 2026-05-24
---

# Phase 8 — Final Validation


> **Plans snapshot (ARCHIVED):** Prefer [`documents/Algorithm/asteroid_lab_08_validation.md`](../../Algorithm/asteroid_lab_08_validation.md). **PR-F (2026-05):** dense server coords removed; island-local only. Do not treat server X/Y / `neighbors4_server` checklists below as current contract.

## Purpose

Assert that the final layout satisfies the solver contract.

## Contract (forbidden, read-only)

The following are **things the validation stage must never do**. On violation, responsibility lies in **other sequences** (candidate·probe·commit·recovery·manual edit), not validation.

```text
Validation must not invent new routes.
Validation must not mutate placement.
Validation must not fix topology.
```

- **No new routes**: do not find paths with `run_route_probe` or fill reservations that did not exist. **Read only** confirmed `RouteReservation`·placement·`TopologyGraph` and check consistency.
- **No placement mutation**: do not add·delete·move confirmed placement such as extractor·extension·occupied cells.
- **No topology modification**: do not add·delete nodes/edges or adjust costs on `TopologyGraph`.

## DTO

`issue_code` is fixed in implementation as **`ValidationIssueCode`** enum (free strings forbidden). Doc/test code strings must match enum values.

```python
@dataclass(frozen=True)
class ValidationIssue:
    issue_code: ValidationIssueCode
    severity: ValidationSeverity
    coord: Coord | None
    candidate_id: str | None
    route_reservation_id: str | None
    path_index: int | None
    route_goal_kind: RouteGoalKind | None
    transport_kind: TransportKind | None
    message: str
```

`route_reservation_id`·`path_index` are **optional** fields for UI cell click·path segment debugging. `None` if absent. If `route_reservation_id` is present, it must be the **same string as Phase 7 `RouteReservation.reservation_id`**.

```python
@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    issues: tuple[ValidationIssue, ...]
```

## Severity

Fixed in implementation as **`ValidationSeverity`** enum. Text below matches member names.

```text
error
warning
info
```

`error` fails validation; `warning`·`info` do not count as failure (see Phase invariant).

## Validation items

```text
all extractor outputs connected
all routes reach a RouteGoal that matches trunk/margin/attachment contract (not “any void cell”)
no orphan transport
no invalid overlap
all Coord satisfy island map grid contract (Phase 1)
transport kind consistency
extension attached to extractor/extension chain
max 3 extensions per extractor
no contradiction between route_domain / reserved path and final placement (read-only comparison only)
reserved_cells and each confirmed reservation's path match collectively
exactly one CONFIRMED RouteReservation exists per confirmed candidate (Phase 7)
each committed placement's candidate_id exists in candidate_pool (else CANDIDATE_POOL_MISSING)
when checking coord contract, sort cell sets with ``_coord_sort_key`` etc. so sorting does not raise on malformed objects
```

## v1+ extensions (documentation only, not v0 required)

The following are candidate checks to reduce **future deadlock·corridor starvation·non-reclaimable** cases. v0 need not implement them; kept for alignment with Overview·Phase 5.

```text
corridor residual capacity (shared corridor remaining pass-slot estimate)
trunk redundancy (risk when single trunk is cut)
route isolation risk (whether alternate path to external goal exists, etc.)
```

## Invariant

```text
[ ] validation is read-only
[ ] Validation must not invent new routes
[ ] Validation must not mutate placement
[ ] Validation must not fix topology
[ ] error severity fails validation
[ ] warning/info does not fail validation
[ ] every issue has explicit issue_code (ValidationIssueCode)
```

## Tests

```text
test_validation_passes_connected_layout
test_validation_fails_unconnected_extractor
test_validation_fails_orphan_transport
test_validation_fails_invalid_coord_contract
test_validation_read_only
test_validation_issue_codes_explicit
test_validation_issue_includes_route_goal_and_transport_context
test_validation_fails_candidate_without_confirmed_reservation
test_validation_fails_reserved_cells_path_mismatch
test_validate_coord_contract_safe_sort_malformed_cell_no_raise
test_validation_fails_committed_candidate_missing_from_pool
```

## Completion criteria

```text
[ ] ValidationResult DTO implemented
[ ] final assert gate implemented
[ ] validation read-only tests pass
```
