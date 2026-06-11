# Contract Brief — Asteroid 10A/10B Stabilization

**Date:** 2026-06-08  
**Status:** APPROVED (plan revision + execution PR-0)  
**Classification:** `contract change` + `implementation change` (tests + minimal L3 `PenaltyMode` in PR-4 only)

## Problem

- L3 rim placement v2(#138–#140) 이후 corridor/congestion/route fragility 회귀가 **재현 가능한 committed fixture 없이** 남아 있음.
- [`test_layer03_route_probe_map_budget.py`](../../tests/unit/asteroid_lab/layers/test_layer03_route_probe_map_budget.py)가 `var/runs/...` 로컬 artifact에 의존해 CI에서 skip됨.
- Canon immediate priority([`asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) §10A/10B) 미착수.
- Replay UI scrub/overlay drift 증상 보고됨 — backend contract와 UI repro 분리 필요.

## Goal

1. **10A:** narrow corridor에서 probe-vs-commit, corridor sharing, transport-kind separation을 결정론적 회귀 테스트로 고정.
2. **10B:** `PenaltyMode.STANDARD` vs `CONSERVATIVE`로 named fragility fixture에서 survivability 개선을 검증 (global superiority 아님).
3. **Large map:** committed `tests/fixtures/asteroid_lab/large_fluid_map/`로 probe budget CI gate un-skip.
4. **Replay:** 10A fixture에 대해 L3 output hash + backend replay frame contract 안정.
5. **Runtime:** 테스트가 `var/runs`에 의존하지 않음.

## Non-goals

- Sequence 12A evolutionary diversity stabilization
- L4 inner fill / L6 commit validate 구현
- L4/L5/L6 routing rewrite
- Sequence 11D full overlay lifecycle (projection cache, partial repaint)
- Replay/artifact/metrics를 solver 입력으로 사용
- `asteroid_miner_layout_lab.js` 변경 (PR-5 four-gate repro 없으면 금지)
- `CONSERVATIVE`가 항상 더 높은 throughput/commit을 낸다는 global assert

## Contract

### Inputs

- Committed fixtures under `tests/fixtures/asteroid_lab/large_fluid_map/` and programmatic narrow-corridor builders.
- Existing L2/L3 stack: `complete_map`, `exterior_plan`, `GeneticSampleSeedSnapshot`, `LayerBudgetContext`.
- PR-4 only: `PenaltyMode` on beam selector (`STANDARD` default).

### Outputs

- Passing regression tests (canon-named, see Acceptance).
- PR-4: `PenaltyMode` StrEnum + beam weight mapping.
- Optional PR-5: minimal JS stale-render guard (four-gate only).

### Invariants (must stay true)

Per [`.cursor/rules/asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc):

- Candidate ≠ commit; commit reprobe on latest `route_domain` is authoritative.
- Corridor same-kind share is soft penalty, not hard reject (§RC).
- Replay/metrics/artifacts are output-only — not solver input.
- Observed survivability metrics (probe-vs-commit drops) are test assertions only in 10B.
- Seeded/deterministic selection; no unseeded randomness in tests.
- Tests load **only** `tests/fixtures/...` or programmatic builders — **never** `var/runs` at runtime.

### Error conditions

- Missing committed large-map fixture → PR-1 blocked until offline generation completes.
- S1 fixture without prior-reservation sequence → invalid test (reject in review).
- 10B assert claiming global `CONSERVATIVE` superiority → contract violation.

### Forbidden behavior

- Runtime `skipif` on local `var/runs` paths.
- Weakening/deleting tests to force green.
- Routing rewrite or L4/L5/L6 algorithm work under this brief.
- UI JS edits without documented deterministic repro + backend contract pass.

## Acceptance criteria

### PR-0 (this document)

- [x] Contract brief written and linked from plan.

### PR-1 — Large fluid map

- [x] `tests/fixtures/asteroid_lab/large_fluid_map/{complete_map,genetic_sample_seeds,game_data_snapshot}.json` committed with README provenance.
- [x] `test_layer03_route_probe_map_budget.py` passes without `skipif`; loads fixtures only.
- [x] `feasible == rim` and `committed >= 0.95 * rim` on large fluid map.

### PR-2 — 10A (S1, S3, S4)

- [x] **S1:** A,B both pool-feasible → A commits → B fails commit reprobe (reservation sequence).
- [x] **S3:** `test_shared_corridor_pressure_regression`, `test_trunk_sharing_penalty_regression` pass under `STANDARD`.
- [x] **S4:** `test_transport_kind_corridor_conflict_regression` — no cross-kind merge.
- [x] **Not in PR-2:** `test_future_expansion_penalty_regression` (→ PR-4).

### PR-3 — Determinism + replay backend

- [x] Same inputs → identical L3 output hash per 10A fixture.
- [x] Replay assembler: monotonic `frame_index`, stable L3 `map_view.overlay_cells`.

### PR-4 — 10B PenaltyMode

- [x] `PenaltyMode` enum + `STANDARD`/`CONSERVATIVE` beam weights (`future_expansion_weight` on CONSERVATIVE).
- [x] **S2:** `test_future_expansion_penalty_regression` on named fixture.
- [x] Named starvation fixtures: `test_route_fragility_reservation_starvation_fixture` — fixture-scoped only.

### PR-5 — UI (optional)

- [x] **Deferred:** no deterministic scrub/overlay repro documented; no `asteroid_miner_layout_lab.js` diff (see Follow-up).

### Validation (each PR merge)

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
ruff check .
mypy django_apps config src
black --check .
```

## Spec / plan links

- **CANON:** [`documents/Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md`](../Algorithm/asteroid_lab_11_future_execution_plan_post_sequence.md) §10A, §10B
- **L3 v2 spec:** [`docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md`](../../docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md)
- **Route probe audit:** [`docs/superpowers/specs/2026-05-31-layer-03-route-probe-reachability-audit.md`](../../docs/superpowers/specs/2026-05-31-layer-03-route-probe-reachability-audit.md)
- **Plan:** `.cursor/plans/asteroid_10ab_stabilization_ffcbd61d.plan.md`
- **Invariants:** [`.cursor/rules/asteroid-lab-invariants.mdc`](../../.cursor/rules/asteroid-lab-invariants.mdc)
- **Testing manual:** [`documents/ai/manuals/testing.md`](manuals/testing.md) §Regression fixtures

## PR sequence

```text
PR-0: contract brief (this file)
PR-1: large_fluid_map fixture + budget test unskip
PR-2: narrow_corridor builders + 10A S1/S3/S4 tests
PR-3: determinism + backend replay frame contract
PR-4: PenaltyMode + 10B fragility (incl. S2)
PR-5: optional UI guard (four-gate only)
```

## Follow-up (PR-5 skipped — 2026-06-08)

Replay UI scrub/overlay drift in `asteroid_miner_layout_lab.js` remains **deferred to Sequence 11D**. No four-gate deterministic repro (steps + fixture/run id) was documented during this initiative; backend PR-3 replay frame contract tests are the stabilization gate here. Next: capture repro on a 10A fixture run, then apply a minimal stale-render guard only if payload contract tests pass and failure isolates to client render state.
