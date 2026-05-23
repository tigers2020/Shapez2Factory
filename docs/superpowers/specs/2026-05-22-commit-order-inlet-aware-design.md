---
status: CANCELLED
cancelled_date: 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
---
# Commit Order ??Inlet-Aware Probe-Fragile-First (Tier 1.2) ??Design Spec

**Status:** Implemented 2026-05-22  
**Parent:** [`2026-05-22-commit-order-probe-fragile-first-design.md`](2026-05-22-commit-order-probe-fragile-first-design.md)  
**Problem:** After T1.1, `commit_route_probe_failed_count: 0` but `commit_inlet_on_shared_transport_count: 3`, `confirmed_count: 21`.

## Approach

`CommitOrderPolicy.INLET_AWARE_PROBE_FRAGILE_FIRST` (pipeline default):

1. **Tier A** ??`fixed_output_transport ????planned_route_cells(others)` ??commit first (probe-fragile sort within tier).
2. **Tier B** ??remaining IDs ??probe-fragile sort.

Multiset preserved; diagnostics include `INLET_ON_SHARED_TRANSPORT` in failed position maps (post-commit only).

## Rollback

`DEFAULT_COMMIT_ORDER_POLICY = CommitOrderPolicy.PROBE_FRAGILE_FIRST`
