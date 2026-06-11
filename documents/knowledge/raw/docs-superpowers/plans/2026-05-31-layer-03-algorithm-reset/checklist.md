# Layer 03 Algorithm Reset — Checklist

**Spec:** [`../../specs/2026-05-31-layer-03-algorithm-reset-design.md`](../../specs/2026-05-31-layer-03-algorithm-reset-design.md)  
**Plan:** [`README.md`](README.md)  
**Status:** DONE (implementation 2026-05-31)

## Gates

- [x] Task 0 — deletion inventory + route_probe evidence
- [x] Task 1 — `Layer03SkipReason.ALGORITHM_RESET`
- [x] Task 2 — RED reset contract tests
- [x] Task 3 — stub `run.py` GREEN
- [x] Task 4 — `algorithm_stub` post-summary
- [x] Task 5 — delete algorithm modules (core + django)
- [x] Task 6 — Django re-export shims
- [x] Task 7 — replay greedy no-op (empty placements already no-op in segment builder)
- [x] Task 8 — delete class-1 tests
- [x] Task 9 — `hard_fail` consumer audit
- [x] Task 10 — stack + django authority tests
- [x] Task 11 — supersede PR-B plan docs
- [x] Task 12 — full verification (A1–A7)

## Verification log

| Command | Result | Date |
|---------|--------|------|
| `pytest tests/unit/asteroid_lab/layers/test_layer_03_reset_stub_contract.py` | pass | 2026-05-31 |
| `pytest tests/unit/asteroid_lab/layers/test_stack_runner_accepts_empty_l3.py` | pass | 2026-05-31 |
| `pytest tests/unit/asteroid_lab/layers/test_no_django_l3_algorithm_authority.py` | pass | 2026-05-31 |
| `pytest tests/unit/asteroid_lab/layers/` | 93 passed | 2026-05-31 |
| `pytest` layers + class-4 replay | 98 passed | 2026-05-31 |
| `ruff check` (touched paths) | pass | 2026-05-31 |

## Notes

- Do **not** use PR-B spec as implementation SoT.
- Do **not** delete `shared/route_probe.py` in this PR.
- Compare skip reason via `Layer03SkipReason` enum in tests; wire values use `.value` on `RimGreedyMetrics.layer_skip_reason` (str field).
