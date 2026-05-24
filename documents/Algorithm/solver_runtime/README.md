---
status: ARCHIVED
owner: solver-runtime-pipeline
last_reviewed: 2026-05-22
archived_reason: Solver optimization pipeline removed; reconstruction-only (see docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md)
---

# Solver Runtime — Solver 버튼 파이프라인

> **Runtime authority (2026-05-24):** Active solver is **RTTP Hybrid C** in `django_apps/asteroid_lab/optimization/` when `ASTEROID_LAB_RTTP_ENABLED=True` — see [`documents/ai/current_plan.md`](../../ai/current_plan.md). This directory documents the **historical Solver-button Phase A–M** orchestration series, not the RTTP implementation contract.

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

## PR ↔ Phase 표 (역사 — 2026-05-22 제거)

2026-05-22 strip surgery로 **PR1–7 코드·`optimization/` 패키지 삭제**. Phase 문서는 `ARCHIVED` 보관.

| PR | Phase | 문서 |
|----|-------|------|
| PR1–7 | A–M | `phase_*.md` — [`strip-solver spec`](../../../docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md) |

**유지:** reconstruction (`phase_a` load 개념은 `reconstruction/`로 이전), Lab replay ([`asteroid_lab_09_replay_timeline.md`](../asteroid_lab_09_replay_timeline.md)), genetic sample admin.

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

## Final Runtime Contract (15단계) — REMOVED 2026-05-22

> 아래 단계는 **삭제된** optimization 파이프라인 역사 계약이다. 현재 `Run Solver` → `SOLVER_NOT_AVAILABLE` only.

Solver 버튼을 눌렀을 때 (역사):

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

## 코드 패키지 — 2026-05-22 strip 직후 (HISTORICAL)

> **HISTORICAL:** 아래 다이어그램은 strip-solver 직후 상태다. **현재 정본**은 [`documents/ai/current_plan.md`](../../ai/current_plan.md) — `optimization/` 는 RTTP Hybrid C로 **복구**되었다.

```text
django_apps/asteroid_lab/reconstruction/   ← ACTIVE (topology, complete)
django_apps/asteroid_lab/contracts/        ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/     ← admin gene templates
django_apps/asteroid_lab/services/solver_runtime_entry.py  ← (2026-05-22) SOLVER_NOT_AVAILABLE stub
django_apps/asteroid_lab/optimization/       ← (2026-05-22) REMOVED
```

### 코드 패키지 — 2026-05-24 현재 (RTTP)

```text
django_apps/asteroid_lab/reconstruction/                       ← ACTIVE
django_apps/asteroid_lab/contracts/                            ← game_data snapshot DTOs
django_apps/asteroid_lab/genetic_sample/                       ← admin gene templates (non-runtime)
django_apps/asteroid_lab/services/solver_runtime_entry.py      ← RTTP runtime entry (config-gated)
django_apps/asteroid_lab/services/lab_rttp_snapshot_compose.py ← 3B-S product timeline projection
django_apps/asteroid_lab/optimization/                         ← RTTP Hybrid C (ACTIVE)
```

HTTP `POST …/run-solver/` 는 유지하나 strip 직후 본문은 stub이었다. 현재는 RTTP runtime 응답을 반환한다 ([`01_entry_point.md`](01_entry_point.md), [`current_plan.md`](../../ai/current_plan.md)).

---

## RTTP pipeline status (2026-05-24)

> **Note:** Frontmatter `ARCHIVED` above is **historical** (2026-05-22 strip surgery). Current `master` runs **RTTP Hybrid C** when `ASTEROID_LAB_RTTP_ENABLED=True`. Code 정본: [`documents/ai/current_plan.md`](../../ai/current_plan.md).

### Track B2-T2: Per-Cell Transport Resolution (CLOSED — PR #62)

> **Plan:** [`2026-05-24-b2-t2-per-cell-transport-resolution.md`](../../../docs/superpowers/plans/2026-05-24-b2-t2-per-cell-transport-resolution.md)  
> **Spec:** [`2026-05-24-b2-t2-per-cell-transport-resolution-design.md`](../../../docs/superpowers/specs/2026-05-24-b2-t2-per-cell-transport-resolution-design.md)

- [x] **Task 1** — `catalog_transport_policy`: lookup + `resolve_cell_transport_kind` (duplicate same-kind last-wins; conflicting kinds fail-closed)
- [x] **Task 2** — `reconstruction_adapter._existing_transport` T2 wire (`lookup` once; `coord=` on policy API)
- [x] **Task 3** — `docs/domain/asteroid_game_data_snapshot.md` T2 paragraph + parent B2 spec cross-link
- [x] **Task 4** — `test_catalog_consumption_boundaries`, catalog/entry transport tests, reconstruction narrow gate, ruff (B2-T2 paths)
- [x] **Task 5** — Ops smoke B (`copy-import-495e552c`, post-merge)

### Track B2-T3: Transport-Aware Route Domain (CLOSED — PR #61)

> **Plan:** [`2026-05-24-b2-t3-transport-aware-route-domain.md`](../../../docs/superpowers/plans/2026-05-24-b2-t3-transport-aware-route-domain.md)  
> **Spec:** [`2026-05-24-b2-t3-transport-aware-route-domain-design.md`](../../../docs/superpowers/specs/2026-05-24-b2-t3-transport-aware-route-domain-design.md)

- [x] **Task 1–4** — `partition_existing_transport`, adapter `blocked_incompatible_transport_cells`, skeleton/route-domain trunk subtract + blocked union, pipeline metrics
- [x] **Task 5** — domain doc + `current_plan` (see repo `documents/ai/current_plan.md`)
- [x] **Ops smoke C** — `test_rttp_transport_kind_route_domain.py` + mixed adapter partition test (mixed-kind 실맵 `run_solver`는 OPS `copy-import` 클래스에서 transport 0 — topology strips transport pre-adapter)

**Next track:** Track D catalog footprint/connector — [`building-catalog-slice-first-consumption-design.md`](../../../docs/superpowers/specs/2026-05-24-building-catalog-slice-first-consumption-design.md) (brainstorming / plan TBD).
