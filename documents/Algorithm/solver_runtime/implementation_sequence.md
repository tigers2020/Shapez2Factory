---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
related_docs:
  - documents/Algorithm/solver_runtime/README.md
---

# Implementation Sequence (PR1–7)

Solver 버튼 **merge·테스트** 순서와 필수 테스트. **Runtime 실행 순서(A→M)와 다름** — [`README.md`](README.md), [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md).

**상태 범례:** `완료` = Runtime PR 계약·테스트 green · `부분` = 코드 있으나 Runtime 체크리스트 잔여 · `미착수` = 모듈/orchestration 없음.

## PR 1 — GeneTemplate (완료)

**Phase:** D  
**문서:** [`phase_d_gene_templates.md`](phase_d_gene_templates.md)

### 작업

- [x] `GeneTemplate` DTO
- [x] `GeneTemplateLoader`
- [x] `coord_transform`
- [x] `gene_projection`
- [x] fixture json
- [x] tests

### 모듈

```text
django_apps/asteroid_lab/optimization/gene_template.py
django_apps/asteroid_lab/optimization/gene_template_loader.py
django_apps/asteroid_lab/optimization/gene_projection.py
django_apps/asteroid_lab/optimization/coord_transform.py
tests/fixtures/asteroid_lab/gene_templates/
tests/unit/asteroid_lab/test_gene_template_loader.py
tests/unit/asteroid_lab/test_gene_projection.py
```

---

## PR 1B — Reconstruction → OptimizationInput (완료)

**Phase:** A, B  
**문서:** [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md), [`phase_b_optimization_input.md`](phase_b_optimization_input.md)  
**코드:** `reconstruction_adapter.py`, `input_contracts.py`, `route_domain.py`, `tests/unit/asteroid_lab/test_optimization_input.py`

### 작업

- [x] `OptimizationInput` DTO·enum (1A, `asteroid_lab/optimization/`)
- [x] `optimization_input_from_reconstruction` · `build_topology_graph`
- [x] `RouteDomainSnapshotBuilder` 시드
- [x] `LoadedReconstructionSnapshot` 명시 DTO
- [x] §0.3 extension kind 정규화 **adapter 계약 테스트** (`mineable_field_kind`, evidence helpers)
- [x] `optimization_input_from_loaded_snapshot` + 회귀 테스트

### 완료 기준 (Runtime PR1B)

- [x] hole asteroid fixture에서 mineable 유지
- [x] 모든 coord Server X/Y
- [x] optimizer 내부 kind 판정 없음 (legacy camelCase extension 문자열 금지)
- [x] **Runtime PR 표에서 「완료」로 승격** ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §5)

---

## PR 2 — Geometry + Route Probe (완료)

**Phase:** E, F, G (한 PR에 묶음)  
**선행:** **PR2.5** (`planned route_goals` — Phase C)  
**문서:** [`phase_e_gene_projection.md`](phase_e_gene_projection.md), [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md), [`phase_g_route_probe.md`](phase_g_route_probe.md)

### 작업

- [x] `candidate_geometry.py`
- [x] `route_probe.py`
- [x] route_domain `provisional_blocked_cells=` + `build_route_domain_for_projected_gene_probe`
- [x] `test_candidate_geometry.py`
- [x] `test_route_probe.py`
- [x] 신규 테스트명: `route_probe_start_*` ([`00_core_principles.md`](00_core_principles.md) §0.7)

### 필수 테스트 (PR2)

```text
test_geometry_accepts_valid_projected_gene
test_geometry_rejects_extractor_not_rim
test_geometry_rejects_extension_not_mineable
test_geometry_rejects_occupied_outside_asteroid
test_geometry_rejects_route_probe_start_inside_occupied   # not output_stub_*
test_geometry_rejects_route_probe_start_invalid_coord     # not output_stub_*
test_geometry_does_not_mutate_optimization_input
test_route_probe_reaches_goal_on_open_domain
test_route_probe_returns_no_goal_cells_when_filtered_goals_empty
test_route_probe_respects_hard_blocked_cells
test_route_probe_respects_transport_mask
test_route_probe_budget_exceeded
test_route_probe_selects_goal_by_priority_weighted_score
test_route_probe_uses_route_probe_start_not_fixed_output_transport
```

---

## PR 2.5 — Capacity / RouteGoal Planner (완료)

**Phase:** C  
**문서:** [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)

### 작업

- [x] `capacity_planner.py`
- [x] `route_goal_planner.py`
- [x] `capacity_plan` DTO
- [x] shape/fluid trunk count (12 / 72)

### 필수 테스트 (PR2.5)

```text
test_capacity_planner_estimates_shape_goal_count_by_12
test_capacity_planner_estimates_fluid_goal_count_by_72
test_route_goal_planner_creates_multiple_external_margin_goals
test_route_goal_planner_does_not_materialize_transport
test_route_goal_planner_distributes_goals_by_quadrant
```

---

## PR 3 — Candidate Pool

**Phase:** H  
**문서:** [`phase_h_candidate_pool.md`](phase_h_candidate_pool.md)

### 작업

- [x] `candidate_dtos.py` (`GeneCandidate`, factory)
- [x] `candidate_equivalence.py`
- [x] `candidate_generator.py`
- [x] normal/rejected split
- [x] dedupe/truncate

### 필수 테스트 (PR3)

```text
test_candidate_generator_reachable_only_enters_normal_pool
test_candidate_generator_rejects_unreachable
test_candidate_generator_dedupes_before_max_candidates
test_candidate_generator_does_not_commit_placements
test_candidate_generator_uses_server_coords_only
test_candidate_id_is_deterministic
```

---

## PR 4 — Candidate Selection v0

**Phase:** I  
**문서:** [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)

### 작업

- [x] `candidate_score.py`
- [x] capacity-aware greedy selector (`candidate_selector.py`)
- [x] `SelectedCandidatePlan`

### 필수 테스트 (PR4)

```text
test_candidate_selector_prefers_high_throughput_low_cost
test_candidate_selector_penalizes_saturated_goal
test_candidate_selector_is_deterministic
```

---

## PR 5 — Incremental Commit

**Phase:** J  
**문서:** [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md)

### 작업

- [x] `commit_best_candidates.py`
- [x] commit-time reprobe
- [x] `RouteReservation`
- [x] rollback / skip
- [x] trunk load update

### 필수 테스트 (PR5)

```text
test_incremental_commit_reprobes_latest_domain
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_updates_goal_load
test_incremental_commit_separates_shape_and_fluid_domains
```

---

## PR 6 — Route Materialization

**Phase:** K  
**문서:** [`phase_k_route_materialization.md`](phase_k_route_materialization.md)

### 작업

- [ ] `route_network_materializer.py`
- [ ] path graph aggregation
- [ ] belt/pipe sprite kind selection
- [ ] merger/splitter/triple conversion

### 필수 테스트 (PR6)

```text
test_route_materializer_creates_straight_and_turns
test_route_materializer_merges_same_kind_shared_paths
test_route_materializer_rejects_shape_fluid_overlap
test_route_materializer_selects_y_or_triple_merger
```

---

## PR 7 — Final Validation + Persist + Replay + Button Pipeline

**Phase:** L, M, Entry  
**문서:** [`phase_l_final_validation.md`](phase_l_final_validation.md), [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md), [`01_entry_point.md`](01_entry_point.md)

**재구현 금지:** Lab optimization replay persist/read/HUD ([`asteroid_lab_12`](../asteroid_lab_12_runtime_replay_wiring.md) 12F–12L 등). **thin adapter** + 신규 `event_type`만.

### 작업

- [ ] validation extension (read-only)
- [ ] `solver_summary`
- [ ] 기존 optimization replay writer/reader에 Runtime 이벤트 **연결** (재구현 아님)
- [ ] UI payload attach (기존 Lab JS·`SolverRun.config_json` 경로)
- [ ] A→M orchestration wiring

### 필수 테스트 (PR7)

```text
test_solver_button_pipeline_persists_result
test_solver_button_pipeline_emits_replay_events
test_solver_button_pipeline_validation_read_only
test_solver_button_pipeline_no_implicit_lab_optimization_sync
```

---

## 권장 구현 순서 (의존성)

```text
PR1 (완료) → PR1B → PR2.5 → PR2 → PR3 → PR4 → PR5 → PR6 → PR7
```

PR2.5는 PR2·PR3 이전에 `route_goals`가 필요하므로 **PR1B 직후** 권장.
