---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
related_docs:
  - documents/Algorithm/solver_runtime/README.md
---

# Implementation Sequence (PR1??)

Solver ë²„íŠ¼ **mergeÂ·?ŒìŠ¤??* ?œì„œ?€ ?„ìˆ˜ ?ŒìŠ¤?? **Runtime ?¤í–‰ ?œì„œ(A?’M)?€ ?¤ë¦„** ??[`README.md`](README.md), [`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md).

**?íƒœ ë²”ë?:** `?„ë£Œ` = Runtime PR ê³„ì•½Â·?ŒìŠ¤??green Â· `ë¶€ë¶? = ì½”ë“œ ?ˆìœ¼??Runtime ì²´í¬ë¦¬ìŠ¤???”ì—¬ Â· `ë¯¸ì°©?? = ëª¨ë“ˆ/orchestration ?†ìŒ.

## PR 1 ??GeneTemplate (?„ë£Œ)

**Phase:** D  
**ë¬¸ì„œ:** [`phase_d_gene_templates.md`](phase_d_gene_templates.md)

### ?‘ì—…

- [x] `GeneTemplate` DTO
- [x] `GeneTemplateLoader`
- [x] `coord_transform`
- [x] `gene_projection`
- [x] fixture json
- [x] tests

### ëª¨ë“ˆ

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

## PR 1B ??Reconstruction ??OptimizationInput (?„ë£Œ)

**Phase:** A, B  
**ë¬¸ì„œ:** [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md), [`phase_b_optimization_input.md`](phase_b_optimization_input.md)  
**ì½”ë“œ:** `reconstruction_adapter.py`, `input_contracts.py`, `route_domain.py`, `tests/unit/asteroid_lab/test_optimization_input.py`

### ?‘ì—…

- [x] `OptimizationInput` DTOÂ·enum (1A, `asteroid_lab/optimization/`)
- [x] `optimization_input_from_reconstruction` Â· `build_topology_graph`
- [x] `RouteDomainSnapshotBuilder` ?œë“œ
- [x] `LoadedReconstructionSnapshot` ëª…ì‹œ DTO
- [x] Â§0.3 extension kind ?•ê·œ??**adapter ê³„ì•½ ?ŒìŠ¤??* (`mineable_field_kind`, evidence helpers)
- [x] `optimization_input_from_loaded_snapshot` + ?Œê? ?ŒìŠ¤??

### ?„ë£Œ ê¸°ì? (Runtime PR1B)

- [x] hole asteroid fixture?ì„œ mineable ? ì?
- [x] ëª¨ë“  coord Server X/Y
- [x] optimizer ?´ë? kind ?ì • ?†ìŒ (legacy camelCase extension ë¬¸ì??ê¸ˆì?)
- [x] **Runtime PR ?œì—???Œì™„ë£Œã€ë¡œ ?¹ê²©** ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) Â§5)

---

## PR 2 ??Geometry + Route Probe (?„ë£Œ)

**Phase:** E, F, G (??PR??ë¬¶ìŒ)  
**? í–‰:** **PR2.5** (`planned route_goals` ??Phase C)  
**ë¬¸ì„œ:** [`phase_e_gene_projection.md`](phase_e_gene_projection.md), [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md), [`phase_g_route_probe.md`](phase_g_route_probe.md)

### ?‘ì—…

- [x] `candidate_geometry.py`
- [x] `route_probe.py`
- [x] route_domain `provisional_blocked_cells=` + `build_route_domain_for_projected_gene_probe`
- [x] `test_candidate_geometry.py`
- [x] `test_route_probe.py`
- [x] ? ê·œ ?ŒìŠ¤?¸ëª…: `route_probe_start_*` ([`00_core_principles.md`](00_core_principles.md) Â§0.7)

### ?„ìˆ˜ ?ŒìŠ¤??(PR2)

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

## PR 2.5 ??Capacity / RouteGoal Planner (?„ë£Œ)

**Phase:** C  
**ë¬¸ì„œ:** [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)

### ?‘ì—…

- [x] `capacity_planner.py`
- [x] `route_goal_planner.py`
- [x] `capacity_plan` DTO
- [x] shape/fluid trunk count (12 / 72)

### ?„ìˆ˜ ?ŒìŠ¤??(PR2.5)

```text
test_capacity_planner_estimates_shape_goal_count_by_12
test_capacity_planner_estimates_fluid_goal_count_by_72
test_route_goal_planner_creates_multiple_external_margin_goals
test_route_goal_planner_does_not_materialize_transport
test_route_goal_planner_distributes_goals_by_quadrant
```

---

## PR 3 ??Candidate Pool

**Phase:** H  
**ë¬¸ì„œ:** [`phase_h_candidate_pool.md`](phase_h_candidate_pool.md)

### ?‘ì—…

- [x] `candidate_dtos.py` (`GeneCandidate`, factory)
- [x] `candidate_equivalence.py`
- [x] `candidate_generator.py`
- [x] normal/rejected split
- [x] dedupe/truncate

### ?„ìˆ˜ ?ŒìŠ¤??(PR3)

```text
test_candidate_generator_reachable_only_enters_normal_pool
test_candidate_generator_rejects_unreachable
test_candidate_generator_dedupes_before_max_candidates
test_candidate_generator_does_not_commit_placements
test_candidate_generator_uses_island_coords_only
test_candidate_id_is_deterministic
```

---

## PR 4 ??Candidate Selection v0

**Phase:** I  
**ë¬¸ì„œ:** [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)

### ?‘ì—…

- [x] `candidate_score.py`
- [x] capacity-aware greedy selector (`candidate_selector.py`)
- [x] `SelectedCandidatePlan`

### ?„ìˆ˜ ?ŒìŠ¤??(PR4)

```text
test_candidate_selector_prefers_high_throughput_low_cost
test_candidate_selector_penalizes_saturated_goal
test_candidate_selector_is_deterministic
```

---

## PR 5 ??Incremental Commit

**Phase:** J  
**ë¬¸ì„œ:** [`phase_j_incremental_commit.md`](phase_j_incremental_commit.md)

### ?‘ì—…

- [x] `commit_best_candidates.py`
- [x] commit-time reprobe
- [x] `RouteReservation`
- [x] rollback / skip
- [x] trunk load update

### ?„ìˆ˜ ?ŒìŠ¤??(PR5)

```text
test_incremental_commit_reprobes_latest_domain
test_incremental_commit_confirms_connected_candidate
test_incremental_commit_rolls_back_unreachable_candidate
test_incremental_commit_updates_goal_load
test_incremental_commit_separates_shape_and_fluid_domains
```

---

## PR 6 ??Route Materialization

**Phase:** K  
**ë¬¸ì„œ:** [`phase_k_route_materialization.md`](phase_k_route_materialization.md)

### ?‘ì—…

- [x] `route_network_materializer.py`
- [x] path graph aggregation
- [x] belt/pipe sprite kind selection
- [x] merger/splitter/triple conversion
- [x] K2 `placement_network_materializer.py` ??CONFIRMED equipment + `merge_materialized_layout`

### ?„ìˆ˜ ?ŒìŠ¤??(PR6)

```text
test_route_materializer_creates_straight_and_turns
test_route_materializer_merges_same_kind_shared_paths
test_route_materializer_rejects_shape_fluid_overlap
test_route_materializer_selects_y_or_triple_merger
```

### K2 placement tests

```text
tests/unit/asteroid_lab/test_placement_materializer.py
```

---

## PR 7 ??Final Validation + Persist + Replay + Button Pipeline

**Phase:** L, M, Entry  
**ë¬¸ì„œ:** [`phase_l_final_validation.md`](phase_l_final_validation.md), [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md), [`01_entry_point.md`](01_entry_point.md)

**?¬êµ¬??ê¸ˆì?:** Lab optimization replay persist/read/HUD ([`asteroid_lab_12`](../asteroid_lab_12_runtime_replay_wiring.md) 12F??2L ??. **thin adapter** + ? ê·œ `event_type`ë§?

### ?‘ì—…

- [x] validation extension (read-only) ??`final_validation.py`
- [x] `solver_summary` ??`SolverRun.config_json["solver_summary"]`
- [x] Runtime replay thin adapter ??`runtime_replay_recorder.py` + `optimization_replay_persist.py` + `optimization_ui_payload.py` (12F v0, `asteroid_lab` ?•ë³¸)
- [x] UI payload attach (`asteroid_lab_page_context` ?½ê¸°) ??PR8 `optimization_replay_read.py`
- [x] A?’M orchestration ??`solver_runtime_pipeline.run_solver_runtime_pipeline`

### ëª¨ë“ˆ

```text
django_apps/asteroid_lab/optimization/final_validation.py
django_apps/asteroid_lab/optimization/pipeline_result.py
django_apps/asteroid_lab/optimization/replay_frame.py
django_apps/asteroid_lab/services/solver_runtime_pipeline.py
django_apps/asteroid_lab/services/runtime_replay_recorder.py
django_apps/asteroid_lab/services/optimization_ui_payload.py
django_apps/asteroid_lab/services/optimization_replay_persist.py
tests/unit/asteroid_lab/test_final_validation.py
tests/unit/asteroid_lab/test_optimization_ui_payload.py
tests/unit/asteroid_lab/test_optimization_replay_persist.py
tests/unit/asteroid_lab/test_solver_runtime_pipeline.py
tests/integration/asteroid_lab/test_solver_button_pipeline.py
```

### ?„ìˆ˜ ?ŒìŠ¤??(PR7)

```text
test_solver_button_pipeline_persists_result
test_solver_button_pipeline_emits_replay_events
test_solver_button_pipeline_validation_read_only
test_solver_button_pipeline_no_implicit_lab_optimization_sync
```

---

## PR 8 ??HTTP Entry + Optimization Page Context (ë°±ì—”??

**Phase:** Entry, M (read)  
**ë¬¸ì„œ:** [`01_entry_point.md`](01_entry_point.md)

### ?‘ì—…

- [x] `POST /asteroid-miner-layout/p/<slug>/run-solver/` ??`asteroid_miner_layout_project_run_solver`
- [x] `solver_runtime_entry.run_solver_runtime_for_project`
- [x] `optimization_replay_payload_for_project` + `lab_page_context` `optimization_replay`
- [x] SSR `lab-optimization-replay-data` json_script
- [x] Lab JS `Run Solver` fetchÂ·HUD (PR9)

### ëª¨ë“ˆ

```text
django_apps/asteroid_lab/services/solver_runtime_entry.py
django_apps/asteroid_lab/services/optimization_replay_read.py
django_apps/web/services/asteroid_lab_page_context.py
django_apps/web/views/public_pages.py
config/settings.py  # ASTEROID_LAB_RUNTIME_GENE_TEMPLATES_PATH
tests/unit/web/test_asteroid_lab_page_context.py  # optimization replay cases
tests/unit/asteroid_lab/test_solver_runtime_entry.py
tests/integration/web/test_asteroid_run_solver.py
```

### ?„ìˆ˜ ?ŒìŠ¤??(PR8)

```text
test_lab_page_context_includes_empty_optimization_replay_when_no_solver_run
test_lab_page_context_reads_persisted_optimization_replay
test_lab_page_context_malformed_optimization_replay_does_not_crash
test_lab_page_context_optimization_replay_does_not_touch_lab_replay_orm
test_solver_runtime_entry_persists_replay_and_summary
test_solver_runtime_entry_does_not_create_lab_replay_frames
test_solver_runtime_entry_requires_map_input
test_post_run_solver_json_persists_and_returns_payload
test_post_run_solver_unknown_slug_404
test_post_run_solver_no_map_input_400
test_get_project_page_includes_optimization_replay_after_run
```

---

## PR 9 ??Lab Run Solver JS + Optimization Replay HUD (12H)

**Phase:** M (UI read)  
**ë¬¸ì„œ:** [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) Â§12H

### ?‘ì—…

- [x] `#lab-optimization-replay-*` HUD ?¸ë“œ (SSR)
- [x] `data-lab-run-solver-url` on `#lab-root`
- [x] `normalizeOptimizationReplayTrack` Â· `renderOptimizationReplayHud` Â· `replaceOptimizationReplayPayload`
- [x] `#lab-header-run` ??POST run-solver (Lab timeline play??`#lab-timeline-play`ë§?

### ëª¨ë“ˆ

```text
django_apps/web/templates/web/asteroid_miner_layout_solver.html
django_apps/web/static/web/js/asteroid_miner_layout_lab.js
tests/unit/web/test_asteroid_lab_page_context.py  # JS smoke ?•ì¥
tests/integration/web/test_asteroid_run_solver.py
tests/integration/web/test_asteroid_lab_optimization_replay_hud.py
```

### ?„ìˆ˜ ?ŒìŠ¤??(PR9)

```text
test_lab_template_includes_optimization_replay_hud_nodes
test_lab_js_replay_wiring_smoke  # optimization replay + run-solver wiring
test_post_run_solver_json_updates_page_context_track
test_run_solver_response_does_not_include_lab_replay_frames
```

---

## ê¶Œì¥ êµ¬í˜„ ?œì„œ (?˜ì¡´??

```text
PR1 (?„ë£Œ) ??????PR8 ??PR9
```

PR2.5??PR2Â·PR3 ?´ì „??`route_goals`ê°€ ?„ìš”?˜ë?ë¡?**PR1B ì§í›„** ê¶Œì¥.
