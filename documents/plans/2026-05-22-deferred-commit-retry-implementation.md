# Deferred Commit Retry — Implementation Plan (C-GATE)

**Spec:** [`docs/superpowers/specs/2026-05-22-deferred-commit-retry-design.md`](../../docs/superpowers/specs/2026-05-22-deferred-commit-retry-design.md) (Approved)

## Vertical slices (TDD)

1. `test_deferred_retry_rounds_zero_matches_single_pass_outcome` — `deferred_retry_rounds=0` parity
2. `test_deferred_retry_recovers_order_dependent_probe_failure` — queue + 1 round recovery
3. `test_deferred_retry_does_not_retry_inlet_skip` / `test_deferred_retry_does_not_queue_occupied_conflict`
4. Refactor `commit_selected_candidates` + `CommitDiagnostics` + pipeline summary fields
5. Manual solver re-run — C-GATE on reference asteroid

## Status

Slices 1–4 implemented. Slice 5 = user verification.
