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

# Phase J ??Incremental Commit

## ëª©ì 

? íƒ??candidateë¥??¤ì œ layout ?„ë³´ë¡?**?•ì •**?œë‹¤. commit-time probeê°€ ? ì¼???°ê²° ì¦ëª…?´ë‹¤.

## ?…ë ¥

```text
SelectedCandidatePlan
OptimizationInput (latest route_domain ?„ì )
```

## ?°ì¶œë¬?

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

## ?‘ì—…

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

deferred retry (v0, C-GATE ??[`deferred-commit-retry`](../../../docs/superpowers/specs/2026-05-22-deferred-commit-retry-design.md)):
  primary pass queues ROUTE_PROBE_FAILED only (Variant A ??not in skipped until retry exhausted)
  one deterministic retry round in plan order on latest domain
  max_retry_rounds default 1; 0 disables (legacy single-pass)
```

### Commit-time probe is authoritative

```text
commit success proof = latest route_domain reprobe
```

candidate phase route result??ì°¸ê³ ?©ë§Œ.

### Route sharing (v0 ??[`shared-transport-inlet`](../../../docs/superpowers/specs/2026-05-22-shared-transport-inlet-design.md))

- **?ˆìš©:** same `TransportKind` route path / reserved cells **ê³µìœ ** (merge trunk)
- **ê¸ˆì?:** `fixed_output_transport` ê°€ ?´ë? committed transport cell ?„ì— ?“ì„ (`INLET_ON_SHARED_TRANSPORT`) ???…êµ¬ ë´‰ì‡„
- **?ˆìš©:** extension coord ê°€ committed transport cell ??(shared trunk; K2 transport wins) ??[`commit-extension-shared-trunk`](../../../docs/superpowers/specs/2026-05-22-commit-extension-shared-trunk-design.md)
- **ê¸ˆì?:** `occupied_cells` (extractor+extensions) êµì§‘??(`OCCUPIED_CELL_CONFLICT`)
- **ê¸ˆì?:** shape belt vs fluid pipe ?™ì¼ cell (`TRANSPORT_KIND_CONFLICT`)

### Capacity

commit ?´í›„ edge / goal load ?„ì . `load >= capacity`?´ë©´ ?™ì¼ edge/goal ?¬ìš© ?„ë³´??high cost ?ëŠ” reject ([OD-3](open_decisions.md)).

## ê¸ˆì?

- candidate probeë§Œìœ¼ë¡?commit ?•ì • ([Â§0.5](00_core_principles.md))
- `route_domain` in-place mutation (`RouteDomainSnapshotBuilder` ?¬ë¹Œ?œë§Œ)
- validation?ì„œ repair

## ?„ë£Œ ì¡°ê±´

- [x] confirmed candidateë§ˆë‹¤ ìµœì‹  domain reprobe ?±ê³µ
- [x] ?¤íŒ¨ candidate rollback/skip deterministic
- [x] goal loadÂ·reservation ?íƒœ ê°±ì‹ 
- [x] shape/fluid domain ë¶„ë¦¬

## ?„ìˆ˜ ?ŒìŠ¤??

```text
test_incremental_commit_reprobes_latest_domain
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_updates_goal_load
test_incremental_commit_separates_shape_and_fluid_domains
```

## RouteDomainSnapshotBuilder (commit)

| API | commit ?¬ìš© |
|-----|-------------|
| `build_snapshot(..., confirmed_reservations, committed_occupied_cells)` | **?•ë³¸** ??ë§??œë„ ì§ì „Â·?±ê³µ ???¬ë¹Œ??|
| `build_seed_snapshot` | ?œë“œë§?|
| `build_commit_snapshot` | ë¯¸êµ¬?„Â·ì„ ??deprecated wrapper ??semantics ê¸ˆì? |

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- êµ¬í˜„: `commit_best_candidates.py` (`commit_selected_candidates`)
- ?ŒìŠ¤?? `tests/unit/asteroid_lab/test_incremental_commit.py`
- [`asteroid_lab_07_incremental_commit.md`](../asteroid_lab_07_incremental_commit.md)

## ?¤ìŒ Phase

??[`phase_k_route_materialization.md`](phase_k_route_materialization.md)
