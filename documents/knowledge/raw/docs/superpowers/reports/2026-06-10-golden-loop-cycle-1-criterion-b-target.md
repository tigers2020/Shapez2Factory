# Golden Loop Cycle 1 — align L4 cap with Criterion B

## Baseline (cycle-0)

- branch: `master` @ `c4f1f573`
- command: `python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy --out-dir var/experiments/golden_loop/cycle-0`
- `valid=true`, `routeable_group_count=130`, `inner_routeable_group_count=54`
- `meets_inner_target_b=false`, `routeable_gap_to_target_b=1`
- L5 failures: none

## Diagnosis

- dominant bucket: **target mismatch** — L4 greedy cap used `target_routeable_group_count_for_field` (90% → 130 total), while Criterion B requires 131 (76 rim + 55 inner @ 80%)
- `max_inner_routeable = 130 - 76 = 54` hard-stopped placement one group short; not a footprint failure

## Hypothesis

- Pass Criterion B total routeable target (131) into golden solver L4 via `target_routeable_group_count` after L3 rim count is known.

## Change

- `layer04_inner_fill.py`: `CRITERION_B_INNER_FILL_RATIO`, `min_total_routeable_target_for_field`
- `golden_fixture_solver_run.py`: `use_l4_criterion_b_target=True` (default), `_run_golden_inner_pattern_fill`
- `test_golden_l4_capacity_metrics.py`: expect `meets_l4_inner_target_b=True`

## Verification

- `python scripts/run_golden_loop.py --throughput-targets 80 --write-best-copy --out-dir var/experiments/golden_loop/cycle-1`
- `routeable_group_count=131`, `inner_routeable_group_count=55`, `meets_inner_target_b=True`, `routeable_gap_to_target_b=0`
- `valid=true`, L5 failure histogram empty
- `pytest tests/unit/asteroid_lab/experiments/test_golden_l4_capacity_metrics.py -q` → 3 passed
- `powershell -File scripts/test_fast.ps1` → 1876 passed

## Decision

- **SUCCESS** — Criterion B target met in one cycle
- branch: `feat/golden-loop-criterion-b-target`
- PR: (pending user request)
- deferred: inner eval throughput (PR-17 / routed_throughput still 30960 rim-only); Q-template L5 catalog
