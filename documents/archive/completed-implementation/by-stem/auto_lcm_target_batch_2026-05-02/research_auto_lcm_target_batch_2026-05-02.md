# Research: Auto LCM target batch (2026-05-02)

## Context

- `compute_factory_batch` already computes `minimal_balanced_target_count` from per-base `quadrants_per_target` and `FULL_SOURCE_CAPACITY` (4), via LCM of per-kind alignment factors.
- `compute_base_demands` previously called `compute_factory_batch(..., requested_target_count=manual, auto_balance=False)`, so user-supplied `target_count` overrode the balanced batch.

## Decision

- Product path uses only `compute_factory_batch(target)` with the single auto path (no manual override).
- Unsupported factory targets (multi-layer, pin/crystal): no batch; graph uses `target_count=1`.

## References

- `django_apps/shapez_solver/domain/factory_demand.py`
