---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-20
phase: I
pr: 4
related_docs:
  - documents/Algorithm/solver_runtime/open_decisions.md
  - documents/Algorithm/asteroid_lab_06_evolutionary_search.md
---

# Phase I — Candidate Selection v0

## 목적

**Solver Button v0 정본 선택기** — capacity-aware **greedy** only. Candidate pool에서 **commit 시도 순서**를 만든다. 아직 확정 배치가 아니다.

> **GA 미사용:** [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md) · `Genome`/`Gene.commit_order` 는 **legacy reference** ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §3).

## RD-GATE lab reference (2026-05-23)

Reference `copy-import-e954a2cb` passes RD-GATE with **lab** `run_config`:

| Key | Value |
|-----|-------|
| `mode` | `lab` |
| `selection_shadow_policy` | `shadow_domain_parity` |
| `selection_commit_order_strategy` | `off` (Phase J `CommitOrderPolicy` overlay) |
| `route_probe_max_expansions` | **512** (256 alone stalls selection ≈20) |

Script: `python scripts/confirm_rd_gate_lab_config.py` → `var/rd_gate_confirm.json`.

Interactive **runtime** (`mode=runtime`, 55s deadline, beam selection, summary-only replay) is separate from this lab gate.

## 입력

```text
CandidatePool (normal)
PlannedRouteGoals / capacity_plan
OptimizationInput
```

## 산출물

```text
SelectedCandidatePlan
ordered candidate ids
```

## 작업

### Phase I inlet mirror (Tier 1.2b)

Hard filter: `fixed_output_transport ∉ selected_route_cells`. Accumulated cells use the **full** generation probe path (`selection_mirror_route_cells`), not only the normalized tail (`planned_route_cells`), so prefix trunk coords are not dropped before commit reprobe.

### Phase I′ shadow domain parity (reprobe drift)

Pipeline default: `SelectionShadowPolicy.SHADOW_DOMAIN_PARITY`. Greedy selection maintains in-memory `SelectionShadowState` and calls `shadow_try_confirm` (same `RouteDomainSnapshotBuilder` + reprobe budget as Phase J) before ordering each pick. Inlet hard-filter uses shadow **reprobed** `committed_route_cells`, not generation paths. `OFF` restores Tier 1.2b mirror-only behavior (tests / rollback). See [`2026-05-22-reprobe-drift-shadow-domain-design.md`](../../../docs/superpowers/specs/2026-05-22-reprobe-drift-shadow-domain-design.md).

### Phase I′-R shadow stuck recovery

When the primary eligible pool exhausts without a `shadow_try_confirm` success, selection widens to a **recovery pool** (`build_shadow_recovery_pool`): remaining candidates with hard footprint / anchor-slot / inlet-on-committed-route checks only (trunk `goal_load` cap relaxed). Recovery tries candidates in **ascending** score order (lower-ranked survivors first). Hard filters and `shadow_try_confirm` are unchanged. Summary keys: `selection_shadow_stuck_count`, `selection_shadow_recovery_*`, probe-failure reason breakdowns.

### Phase I′-O start-preserving shadow-aware ordering

Primary and recovery pools sort via `shadow_aware_sort_key` (`selection_shadow_ordering.py`): minimize `candidate_future_start_blocker_pressure` (sum of `build_future_start_pressure` over blocked future `route_probe_start` / `fixed_output_transport`), then blocker count, route-cell count, Phase I score. Pick impact is classified as `blocks_future_output_start` > `blocks_future_equipment` > `blocks_future_route_only` for diagnostics. `OFF` keeps legacy `_selection_sort_key`. Diagnostics: `selection_shadow_future_start_blocker_*`, pressure totals, `selection_shadow_start_blocker_kind_counts`, `selection_shadow_blocked_start_pressure_top`.

### Phase M2 — start-preserving commit order (fixed selection set)

After Phase I′ selects candidates, `selection_commit_ordering.py` may reorder **commit attempts only** (`SelectionCommitOrderStrategy.START_PRESERVING_GREEDY` default). Multiset of `ordered_candidate_ids` is preserved; `shadow_try_confirm` simulates each pick. Sort defers `is_start_blocked_now` and future start pressure before score. `OFF` leaves selection order and applies legacy `CommitOrderPolicy`. Optional `START_PRESERVING_BEAM` (`beam_width=4`). Summary: `selection_commit_order_*` keys including `original_prefix` / `planned_prefix`.

### v0 Score

```text
score =
    + throughput_factor * 100
    - route_cost * 5
    - goal_priority * 20
    - estimated_corridor_pressure
    - trunk_load_pressure
    - shared_path_pressure (selected planned route overlap; Tier 1)
    - route_fragility_penalty (v0 = 0 until narrow segments on candidate)
```

### Capacity-aware trunk load

Shape:

```text
trunk capacity = 12 fully boosted platforms
```

Fluid:

```text
trunk capacity = 72 fully boosted platforms
```

```python
load_ratio = assigned_platform_count / capacity_by_transport_kind
```

`goal_assigned_platforms` 값은 **플랫폼 개수** (+1 per bundle). `base_throughput` 합산은 사용하지 않는다 (fully boosted ×16도 1 platform).

### Bundle selection budget (route slot vs miner count)

```text
route_out_count = len(route_goals)
target_miner_bundle_count = sum per goal (
  shape belt goals × miners_per_shape_route (default 12, env ASTEROID_LAB_MINERS_PER_ROUTE_OUT)
  fluid pipe goals × 72 (FLUID_PLATFORMS_PER_GOAL)
)
```

`route_out_count`는 외부 route slot 수; `target_miner_bundle_count`는 선택·commit **시도** 상한(확정 수 아님). 구현: `bundle_selection_targets.py` · `solver_summary` / replay inspector.

**선택 예산 종료(v0):** `target_miner_bundle_count`에 도달하면 `len(ordered_candidate_ids)` 기준으로 종료한다. `base_throughput` 합은 `selected_throughput_at_stop` 진단용만 쓰며, 예산 비교에 사용하지 않는다.

**Footprint 비중복(v0):** greedy 선택 시 이미 고른 후보의 `occupied_cells`와 교차하는 번들은 commit order에 넣지 않는다 (Phase J `occupied_cell_conflict`와 동일 집합 계약).

**Shared transport inlet(v0):** [`shared-transport-inlet`](../../../docs/superpowers/specs/2026-05-22-shared-transport-inlet-design.md) — `fixed_output_transport` 가 이미 선택/committed route cell 위이면 제외; same-kind path cell sharing은 허용.

포화에 가까운 goal은 penalty 증가. **v1 (OD-3):** per-goal platform cap(12/72) 초과 시 alternate `GoalLoadKey` 우선; 전부 overflow면 penalty pool fallback ([OD-3](open_decisions.md)).

### 정책

- capacity-aware **greedy** selector (v0)
- GA는 v1 ([OD-4](open_decisions.md))

## 금지

- selection 단계에서 layout commit
- candidate 생성 enumeration 순서를 commit order로 사용

## 완료 조건

- [x] 동일 pool·plan에서 선택 순서 deterministic
- [x] 고 throughput·저 route cost 후보가 우선
- [x] saturated goal에 penalty 반영

## 필수 테스트

```text
test_candidate_selector_prefers_high_throughput_low_cost
test_candidate_selector_penalizes_saturated_goal
test_candidate_selector_is_deterministic
```

## 관련 코드·문서

- 구현: `candidate_score.py`, `candidate_selector.py` (`select_gene_candidates_greedy`)
- 테스트: `tests/unit/asteroid_lab/test_candidate_selector.py`
- 레거시 GA: [`asteroid_lab_06_evolutionary_search.md`](../asteroid_lab_06_evolutionary_search.md)

## 다음 Phase

→ [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md)
