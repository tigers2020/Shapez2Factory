# L3 reset deletion inventory

**SoT:** [`../../specs/2026-05-31-layer-03-algorithm-reset-design.md`](../../specs/2026-05-31-layer-03-algorithm-reset-design.md)

**Do NOT use:** [`../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md`](../../specs/2026-05-30-layer-03-boundary-m-repack-greedy-design.md) (SUPERSEDED)

## route_probe retention (R7)

```text
2026-05-31 inventory:
  importers of shapez2_factory...shared.route_probe:
    - greedy_pass1.py (DELETE in this PR)
  Action: RETAIN shared/route_probe.py
```

## Test classification

| Path | Class | Action |
|------|-------|--------|
| `test_layer_03_boundary_m_repack_acceptance.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_pass2.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_variants.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_append.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_reservation.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_run.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_anchors.py` | 1 | DELETE |
| `test_layer_03_rim_greedy_seed_orient.py` | 1 | DELETE |
| `test_layer_03_route_goal_builder.py` | 1 | DELETE |
| `test_layer_03_04_skeleton.py` | 1 | DELETE |
| `test_layer03_append_replay_parity.py` | 1 | DELETE |
| `test_layer03_rim_greedy_segment.py` | 1 | DELETE |
| `test_layer03_pool_windowing.py` | 1 | DELETE |
| `test_lab_replay_timeline_layer03_runtime.py` | 1 | DELETE |
| `test_rim_greedy_contracts.py` | 2 | KEEP |
| `test_rim_greedy_append_contracts.py` | 2 | KEEP |
| `test_stack_runner_core_boundary.py` | 3 | KEEP |
| `test_layer03_exterior_connector_overlay_persistence.py` | 4 | KEEP |
| `test_layer03_pattern_bundle_highlights.py` | 4 | KEEP |
| `test_layer_03_l4_boundary.py` | 5 | KEEP |
| `test_layer_04_disabled_shim.py` | 5 | KEEP |
| `test_layer_03_reset_stub_contract.py` | ADD | CREATE |
| `test_stack_runner_accepts_empty_l3.py` | ADD | CREATE |
| `test_no_django_l3_algorithm_authority.py` | ADD | CREATE |

## hard_fail consumer audit (Task 9)

| File | Role |
|------|------|
| `rim_greedy.py` | Sets `hard_fail=True` on empty builder — OK |
| Deleted greedy tests | Removed |
| No `stack_runner` / L5 branch on `hard_fail` alone | Verified 2026-05-31 |
