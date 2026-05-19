---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
---

# Solver Runtime — Solver 버튼 파이프라인

**역할:** Solver Runtime Pipeline Architect  
**목적:** UI `Solver` / `Run Solver` 버튼 클릭 시 실행되는 **E2E 파이프라인 v0** 계약·PR 체크리스트를 고정한다.

> **문서 정체:** **「Solver 버튼 v0 재구현·오케스트레이션 계획」** — 저장소 전체 optimization 미존재를 뜻하지 않는다.  
> **충돌 해소:** [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) (패키지·GA·용어·PR vs 코드·replay).  
> **구현 정본:** 코드·`CANON` 우선. 본 시리즈는 `ACTIVE` / `RESEARCH` 성격.  
> **레거시:** [`asteroid_lab_*`](../) — GA·`BundlePattern`·`shapez_asteroid` 경로는 **참고**; Solver 버튼 merge 순서는 [`implementation_sequence.md`](implementation_sequence.md). [`asteroid_lab_10`](../asteroid_lab_10_development_sequence.md) 을 대체하지 않음.

## 실행 순서 vs 구현(PR) 순서

| 구분 | 순서 | 용도 |
|------|------|------|
| **Runtime execution** | A→B→C→D→E→F→G→H→I→J→K→L→M | 버튼 1회 호출 시 orchestration |
| **Implementation (PR)** | PR1→PR1B→PR2.5→PR2→…→PR7 | merge·리뷰 단위 ([`implementation_sequence.md`](implementation_sequence.md)) |

PR1이 Phase **D**를 먼저 완료한 것은 유전자 계약 고정용이며, 실행 시 D는 C 다음·E 이전이다.

## 파이프라인 요약

```text
DB reconstruction map
→ OptimizationInput
→ capacity / RouteGoal planning
→ GeneTemplate projection
→ geometry validation
→ route probe
→ candidate pool
→ selection
→ incremental commit
→ route materialization
→ validation
→ replay / UI payload
```

**핵심 불변식:** 후보 생성은 탐색일 뿐이며, **증분 커밋만** 확정 배치를 만든다. 상세: [`00_core_principles.md`](00_core_principles.md).

## 읽기 순서

1. [`00_core_principles.md`](00_core_principles.md) — 금지·허용·adapter 필드 정규화  
2. [`01_entry_point.md`](01_entry_point.md) — 트리거·입출력  
3. [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md) ~ [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md) — Phase A–M  
4. [`implementation_sequence.md`](implementation_sequence.md) — PR1–7 체크리스트·필수 테스트  
5. [`open_decisions.md`](open_decisions.md)  
6. [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) — 레거시·코드·PR 상태 충돌 해소 — OD-1–4

## PR ↔ Phase 표 (Runtime 계약·테스트 기준)

**「미착수」** = 해당 PR의 Solver-button 계약·필수 테스트·orchestration 미완. **코드 인벤토리와 별도** — [`ARCHITECTURE_RECONCILIATION.md` §5](ARCHITECTURE_RECONCILIATION.md).

| PR | Runtime 상태 | 코드 스냅샷 | Phase | 문서 |
|----|--------------|-------------|-------|------|
| PR1 | **완료** | `GeneTemplate`·projection green | D | [`phase_d_gene_templates.md`](phase_d_gene_templates.md) |
| PR1B | **완료** | `LoadedReconstructionSnapshot`·§0.3 adapter·회귀 테스트 green | A, B | [`phase_a_*`](phase_a_load_reconstruction.md), [`phase_b_*`](phase_b_optimization_input.md) |
| PR2.5 | **완료** | `capacity_planner`·`route_goal_planner` | C | [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md) |
| PR2 | **완료** | `candidate_geometry`·`route_probe`·`provisional_blocked_cells` | E, F, G | [`phase_e_*`](phase_e_gene_projection.md) ~ [`phase_g_*`](phase_g_route_probe.md) |
| PR3 | **완료** | `candidate_dtos`·`candidate_equivalence`·`candidate_generator` | H | [`phase_h_candidate_pool.md`](phase_h_candidate_pool.md) |
| PR4 | **완료** | `candidate_score`·`candidate_selector` | I | [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md) |
| PR5 | **완료** | `commit_best_candidates`·reservation overlay | J | [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md) |
| PR6 | 미착수 | — | K | [`phase_k_route_materialization.md`](phase_k_route_materialization.md) |
| PR7 | 미착수 | replay **재구현 금지**·thin adapter | L, M, 01 | [`phase_l_*`](phase_l_final_validation.md), [`phase_m_*`](phase_m_persist_replay_ui.md) |

**PR2.5 선행:** Phase C이지만 **PR2 `route_probe`가 `RouteGoal` 집합을 필요**로 하므로, 구현 순서는 **PR1B 직후 PR2.5 → PR2** ([`implementation_sequence.md`](implementation_sequence.md)). 런타임 **실행** 순서는 여전히 B 다음 C.

## 레거시 시리즈와의 관계

| 주제 | Runtime 정본 | 레거시 참고 |
|------|--------------|-------------|
| OptimizationInput·route_domain | phase_b, §0.3 | [`asteroid_lab_01`](../asteroid_lab_01_optimization_input.md) |
| 패턴/유전자 | phase_d (`GeneTemplate`) | [`asteroid_lab_02`](../asteroid_lab_02_pattern_library.md) (`BundlePattern`) |
| Route probe | phase_g | [`asteroid_lab_04`](../asteroid_lab_04_route_probe.md) |
| Commit / validation / replay | phase_j, l, m | [`asteroid_lab_07`](../asteroid_lab_07_incremental_commit.md) ~ [`09`](../asteroid_lab_09_replay_debug.md), [`12`](../asteroid_lab_12_runtime_replay_wiring.md) |
| GA·evolution | **v0 미사용** (greedy만) | [`asteroid_lab_05`](../asteroid_lab_05_genome_fitness.md), [`06`](../asteroid_lab_06_evolutionary_search.md) — legacy reference |

## 처리량 CANON

포화·목표 수 계산: [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../../game_rules/shapez2_asteroid_space_transport_throughput.md).

## Final Runtime Contract (15단계)

Solver 버튼을 눌렀을 때:

```text
1. Load DB reconstruction map.
2. Convert to OptimizationInput.
3. Treat shape/fluid field kinds as mineable field through sets, not direct kind checks.
4. Estimate platform capacity and required RouteGoal count.
5. Create multiple external RouteGoals without installing transport.
6. Load GeneTemplates.
7. Project every gene against rim anchors and rotations.
8. Validate geometry.
9. Probe route from route_probe_start to planned RouteGoals.
10. Build reachable-only CandidatePool.
11. Select candidates with capacity-aware v0 scorer.
12. Incrementally commit with latest-domain re-probe.
13. Materialize shared route network into belt/pipe sprites.
14. Run read-only validation.
15. Persist result and optimization replay payload.
```

```text
Candidate generation explores possibilities.
Only incremental commit creates confirmed layout.
```

## 코드 패키지 (정본)

```text
django_apps/asteroid_lab/optimization/   ← 모든 Runtime PR
django_apps/shapez_asteroid/             ← 제거됨; 문서·import 금지
```

- **있음:** `input_contracts.py`, `enums.py`, `loaded_snapshot.py`, `reconstruction_adapter.py`, `route_domain.py`, PR1 gene 모듈, PR2.5 `capacity_planner`·`route_goal_planner`, PR2 `candidate_geometry`·`route_probe`
- **있음:** PR3 `candidate_dtos.py`·`candidate_equivalence.py`·`candidate_generator.py`
- **예정:** `route_network_materializer.py`, A→M orchestration (PR6–7)
- Lab replay persist/read: `asteroid_lab` + web — PR7에서 **재사용** ([`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md))
