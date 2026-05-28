# Phase 8 — Final Validation

## Purpose

Assert that the final layout satisfies the solver contract.

## Contract (forbidden, read-only)

The following is **what the validation phase must never do**. Violations are responsibility of **other sequences** (candidate·probe·commit·recovery·manual edit), not validation.

```text
Validation must not invent new routes.
Validation must not mutate placement.
Validation must not fix topology.
```

- **No new routes**: do not find paths with `run_route_probe` or fill missing reservations. **Read only** confirmed `RouteReservation`·placement·`TopologyGraph` for consistency checks.
- **No placement mutation**: do not add·delete·move confirmed placement such as extractor·extension·occupied cells.
- **No topology modification**: do not add·delete nodes·edges or adjust costs on `TopologyGraph`.

## DTO

In implementation, `issue_code` is fixed as **`ValidationIssueCode`** enum (no free strings). Doc·test code strings stay identical to enum values.

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

`route_reservation_id`·`path_index` are **optional** fields for UI cell click·path segment debugging. `None` if absent. When `route_reservation_id` present, must be **same string** as Phase 7 `RouteReservation.reservation_id`.

```python
@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    issues: tuple[ValidationIssue, ...]
```

## Severity

In implementation, fixed as **`ValidationSeverity`** enum. Text below stays identical to member names.

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
all Coord satisfy island map grid contract (Phase 1, `CoordFrame.ISLAND_RAW`)
transport kind consistency
extension attached to extractor/extension chain
max 3 extensions per extractor
no contradiction between route_domain / reserved path and final placement (read-only comparison only)
reserved_cells collectively match each confirmed reservation's path
exactly one CONFIRMED RouteReservation exists per confirmed candidate (Phase 7)
each committed placement's candidate_id exists in candidate_pool (else CANDIDATE_POOL_MISSING)
when checking coord contract, sort cell sets with ``_coord_sort_key`` etc. so sort step does not raise on malformed objects
```

## v1+ extensions (docs only, not v0 required)

The following are candidate checks to reduce future deadlock·corridor starvation·non-reclaimable cases. v0 need not implement, but retained for alignment with Overview·Phase 5.

```text
corridor residual capacity (estimated remaining pass slots on shared corridor)
trunk redundancy (risk when single trunk disconnects)
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

## Track D+ catalog placement validation (PR-2, 2026-05-24)

**Not catalog-native generation.** PR-2 adds **mapped-only fail-closed** checks on committed candidates that already carry `catalog_placement_ref`. PR-3 will require catalog-native production candidates.

**DTOs (catalog-specific — do not confuse with Phase 8 `ValidationIssue` above):**

- `django_apps/asteroid_lab/contracts/catalog_validation.py` — `CatalogValidationIssue`, `CatalogValidationResult`, `ValidationSeverity`
- `CatalogPlacementIssueCode` — includes `catalog_slice_missing` (WARNING when slice absent; does not fail validation)

**Semantics:**

```text
had catalog_placement_ref + mapped catalog ERROR (mismatch / not_in_slice / transform_error)
  → validation_passed=false (mapped_fail_closed mode)

no catalog_placement_ref (unmapped synthetic lin_*)
  → WARNING only; validation_passed unchanged until PR-3

catalog_slice missing
  → WARNING + catalog_slice_missing metric; validation_passed unchanged

observe_only mode (PR-1 regression / emergency)
  → catalog step metrics only; validation_passed unchanged
```

**Read-only (same as Phase 8):** `validate_catalog_placements` and `classify_committed_catalog_placements` must not import `probe_route`, `incremental_commit`, or candidate-generation mutation paths. See `tests/unit/asteroid_lab/test_validation_readonly_guards.py`.

**`solver_summary.issue_codes` (output-only, not algorithm input):**

- Top-level `issue_codes` lists **ERROR** catalog codes only when they caused `validation_passed=false`.
- WARNING/INFO catalog codes appear in `algorithm_steps[].metrics` (`catalog_warning_codes`, `catalog_issue_codes`, `catalog_slice_missing`).
- Successful runs with warning-only catalog findings keep `issue_codes == []` (E3/E4 compatible).

**Pipeline default:** `RttpPipelineConfig.catalog_placement_validation_mode = "mapped_fail_closed"`.

## Completion criteria

```text
[ ] ValidationResult DTO implementation
[ ] final assert gate implementation
[ ] validation read-only tests pass
[x] Track D+ PR-2 catalog placement validation (mapped fail-closed; see section above)
```
