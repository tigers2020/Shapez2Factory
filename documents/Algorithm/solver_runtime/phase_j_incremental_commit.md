---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: J
pr: 5
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_07_incremental_commit.md
---

# Phase J ? Incremental Commit

## Purpose

**Confirm** selected candidates as actual layout drafts. Commit-time probe is the authoritative connectivity proof.

## Input

```text
SelectedCandidatePlan
OptimizationInput (latest route_domain accumulated)
```

## Output

```text
Confirmed placements
RouteReservation(s)
updated trunk / goal load
```

## Commit order (before incremental commit)

Phase I produces `SelectedCandidatePlan`; commit order may reorder IDs (same multiset) before Phase J.

| Policy (`CommitOrderPolicy`) | v0 pipeline default (T1.1) | Behavior |
|------------------------------|----------------------------|----------|
| `inlet_aware_probe_fragile_first` | **yes** (T1.2) | Inlet-vulnerable tier first, then probe-fragile within tier ([`2026-05-22-commit-order-inlet-aware-design.md`](../../../docs/superpowers/specs/2026-05-22-commit-order-inlet-aware-design.md)) |
| `probe_fragile_first` | rollback / compare | Total sort only (T1.1) |
| `round_robin_diversity` | tests / rollback | Round-robin across goal/corridor/anchor buckets (`diversify_commit_order`) |

Deferred retry and reprobe rules unchanged; order affects **when** each ID sees the live `route_domain`.

## Tasks

```text
for candidate in selected_order:
    rebuild latest route_domain
    re-run route_probe from route_probe_start
    if failed:
        rollback / skip candidate
    else:
        create RouteReservation
        reserve path
        promote placement to confirmed
        update trunk load

deferred retry (v0, C-GATE ? [`deferred-commit-retry`](../../../docs/superpowers/specs/2026-05-22-deferred-commit-retry-design.md)):
  primary pass queues ROUTE_PROBE_FAILED only (Variant A ? not in skipped until retry exhausted)
  one deterministic retry round in plan order on latest domain
  max_retry_rounds default 1; 0 disables (legacy single-pass)
```

### Commit-time probe is authoritative

```text
commit success proof = latest route_domain reprobe
```

Candidate phase route result is reference only.

### Route sharing (v0 ? [`shared-transport-inlet`](../../../docs/superpowers/specs/2026-05-22-shared-transport-inlet-design.md))

- **Allowed:** same `TransportKind` route path / reserved cells **shared** (merge trunk)
- **Forbidden:** `fixed_output_transport` lands inside existing committed transport cell (`INLET_ON_SHARED_TRANSPORT`) ? mandatory reject
- **Allowed:** extension coord on committed transport cell (shared trunk; K2 transport wins) ? [`commit-extension-shared-trunk`](../../../docs/superpowers/specs/2026-05-22-commit-extension-shared-trunk-design.md)
- **Forbidden:** `occupied_cells` (extractor+extensions) overlap (`OCCUPIED_CELL_CONFLICT`)
- **Forbidden:** shape belt vs fluid pipe same cell (`TRANSPORT_KIND_CONFLICT`)

### Capacity

After commit, edge / goal load accumulated. When `load >= capacity`, same edge/goal reuse gets high cost or reject ([OD-3](open_decisions.md)).

## Forbidden

- Commit confirmation from candidate probe only ([§0.5](00_core_principles.md))
- `route_domain` in-place mutation (rebuild via `RouteDomainSnapshotBuilder` only)
- repair in validation

## Completion criteria

- [x] Each confirmed candidate succeeds on latest domain reprobe
- [x] Failed candidate rollback/skip deterministic
- [x] goal load?reservation state updated
- [x] shape/fluid domain separated

## Prerequisite phase

```text
test_incremental_commit_reprobes_latest_domain
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_updates_goal_load
test_incremental_commit_separates_shape_and_fluid_domains
```

## RouteDomainSnapshotBuilder (commit)

| API | commit usage |
|-----|-------------|
| `build_snapshot(..., confirmed_reservations, committed_occupied_cells)` | **canonical** ? rebuild immediately before?after each attempt |
| `build_seed_snapshot` | seed only |
| `build_commit_snapshot` | unimplemented?legacy deprecated wrapper ? semantics forbidden |

## Related code?documents

- Implementation: `commit_best_candidates.py` (`commit_selected_candidates`)
- Tests: `tests/unit/asteroid_lab/test_incremental_commit.py`
- [`asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md)

## Next Phase

? [`phase_k_route_materialization.md`](phase_k_route_materialization.md)
