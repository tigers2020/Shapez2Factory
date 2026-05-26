# Test Decontamination Inventory (PR-F0 Evidence Report)

**Date:** 2026-05-30  
**Authority:** None — evidence only. Deletions require `PR_F_APPROVED_DELETIONS` in `quarantine_registry.py`.

```text
This report is evidence-only.
It is not a source of deletion authority.
Only PR_F_APPROVED_DELETIONS / PR_F_APPLIED_DELETIONS are mechanical authority.
```

**Spec:** [`../specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md`](../specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md)  
**Prior audit:** [`2026-05-24-test-cleanup-audit.md`](2026-05-24-test-cleanup-audit.md) (PR-E applied)

---

## Status

| Field | Value |
|-------|-------|
| PR-F0 inventory | **COMPLETE** (2026-05-30) |
| Registry sync | `PR_F_AGGRESSIVE_AUDIT_CANDIDATES` = 240 file rows |
| Deletes applied | 0 (`PR_F_APPROVED_DELETIONS` / `PR_F_APPLIED_DELETIONS` empty) |

---

## Summary by grade (F0 complete)

| Grade | Count | Target slice |
|-------|------:|--------------|
| `PROTECTED_CONTRACT` | 229 | — |
| `PROTECTED_REGRESSION` | 0 | — |
| `DUPLICATE_COVERAGE` | 0 | F1 |
| `OBSOLETE_PRODUCT_PATH` | 0 | F2–F4 |
| `PLACEHOLDER_SKIP` | 0 | review |
| `DEFERRED_FEATURE_TEST` | 4 | keep |
| `INTENT_UNKNOWN` | 2 | report |
| `BROKEN_OR_DEAD` | 0 | F1 |
| `ENV_GUARD_SKIP` | 5 | keep |

**Total `test_*.py` inventoried:** 240  
**0-byte test files:** none

Regenerate tables: `python scripts/audit_test_inventory.py`

---

## Tier 1 — Mechanical candidates (F1)

No `BROKEN_OR_DEAD` rows in F0. PR-E already removed 0-byte smoke and duplicate replay node.

---

## Tier 3 — Human review (`INTENT_UNKNOWN`)

| path | reason | replacement |
|------|--------|-------------|
| `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` | Product path superseded; helper contract TBD | `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py` |
| `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` | GA shadow — confirm vs PR-GA-2 before F2 | — |

---

## Per-package tables

### `integration` (12 files)

| path | grade | reason |
|------|-------|--------|
| `tests/integration/api/test_health.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/asteroid_lab/test_rttp_macro_real_map_e2e.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/asteroid_lab/test_rttp_runtime_replay_db.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/test_integration_conftest_contract.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_asteroid_miner_layout_solver.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_asteroid_reset_map.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_asteroid_run_solver.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_auth.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_graph_preview_warm.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_pattern_lab.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |
| `tests/integration/web/test_web_smoke.py` | `PROTECTED_CONTRACT` | HTTP / DB integration smoke for active routes |

### `unit/architecture` (7 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/architecture/test_capacity_complete_map_sot_gates.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_catalog_consumption_boundaries.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_django_app_import_boundaries.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_ga_evolution_no_probe_route.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_optimization_contamination_gates.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_quarantined_paths_do_not_leak.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |
| `tests/unit/architecture/test_repo_map_governance.py` | `PROTECTED_CONTRACT` | Architecture / quarantine / contamination gates |

### `unit/asteroid_lab` (154 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/asteroid_lab/test_asteroid_equipment_projection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_asteroid_lab_ui_strings.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_asteroid_map_coords.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_asteroid_sprite_projection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_asteroid_transport_projection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_b_cs3_validation_gate_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_b_cs4_reconstruction_replay_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_blueprint_equivalence_golden.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_boundary_jsonl.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_building_catalog_slice.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_building_catalog_slice_hash.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_candidate_contracts.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_candidate_placements.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_footprint_policy.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_geometry_transform.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_native_candidate_generator.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_native_generator_arch.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_output_attachment.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_placement_audit.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_placement_contracts.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_placement_validation.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_transport_policy.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_catalog_validation_contracts.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_cell_snapshot_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_cleanup_deconstruct.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_committed_throughput_summary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_complete_map.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_coord_frames_types.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_coord_proof_policy.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_coordinate_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_coordinate_frame_ast_gate.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_coordinate_frame_equivalence.py` | `DEFERRED_FEATURE_TEST` | G3 coordinate equivalence xfail gate (strict=True) |
| `tests/unit/asteroid_lab/test_copy_json_island_local_coords.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_create_copy_code_map_input_populates_decoded_json.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_decode_adapter.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_decoded_blueprint_snapshot.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_decoded_snapshot_island_raw_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_deferred_commit_retry_pr2_policy.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_deferred_commit_retry_pr3_execute.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_deferred_commit_retry_shadow.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_equipment_bundles.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_existing_layout_inspection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_existing_layout_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_experiment_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_export_dense_contiguity.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_field_cells.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_final_validation_route_disjoint.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_fl06_route_reservation_alignment.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_fot_outside_mineable_pr1.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_fot_pr2_outward_rim_void_probe.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_ga_evolution_shadow.py` | `INTENT_UNKNOWN` | Helper vs obsolete product path — human review before F2 |
| `tests/unit/asteroid_lab/test_game_data_contracts.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_game_data_coord_transform_golden.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_game_data_snapshot_adapter.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_game_data_snapshot_determinism.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_game_data_snapshot_provenance.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_gene_template_loader.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_genetic_sample_admin_seed.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_genetic_sample_decode.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_genetic_sample_gene_export.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_genetic_sample_mini_map.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_island_bbox.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_island_extractor_blueprint_defaults.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_equipment_bundle_wire.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_map_reset_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_optimization_milestone_payload.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_replay_projection_context.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_replay_timeline_payload.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_replay_timeline_unified_append.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_replay_track_selection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_screen_grid.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_timeline_adapter.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_timeline_rim_enrichment.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_lab_unified_replay_append.py` | `INTENT_UNKNOWN` | Helper vs obsolete product path — human review before F2 |
| `tests/unit/asteroid_lab/test_macro_commit_hud.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_map_overwrite_updated_at.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_miner_placement_topology.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_models.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_official_canonical_export.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_optimization_input_adapter.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_optimization_input_coord_frame.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_persistence_does_not_read_replay_frames.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_placement_goal.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_placement_overlay_import_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_placement_overlay_projection.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_project_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_projection_compat_metrics.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_projection_import_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_projection_source.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstructed_asteroid_persist.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_blueprint_export.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_capacity_summary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_confidence_field_cells.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_island.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_persist_full_map_bbox.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_regression_overclose.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_replay_merge.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_reconstruction_topology.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_event_coverage_matrix.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_limits.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_pipeline_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_recorder.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_snapshot_contract.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_snapshot_events.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_replay_timeline_dto.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rim_highlight.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rim_highlight_layer_boundary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_candidate_generator.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_commit.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_commit_fot_conflict.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_commit_survivability.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_db_macro_integration.py` | `DEFERRED_FEATURE_TEST` | PR-B macro 4x4 pause; permanent skip until child-pool fixture |
| `tests/unit/asteroid_lab/test_rttp_db_replay_sink.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_existing_trunk.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_ga_evolution_pr_ga_2.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_greedy_regret.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_lab_fot_acceptance_fixture.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_lift_lane_domain.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_lns.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_macro_bundle_t3.py` | `DEFERRED_FEATURE_TEST` | PR-B macro 4x4 pause; permanent skip until child-pool fixture |
| `tests/unit/asteroid_lab/test_rttp_macro_dtos.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_milestone_contract.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_milestone_event_types.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_narrow_corridor.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_pipeline_catalog_audit.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_pipeline_greenfield.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_pipeline_macro_greenfield.py` | `DEFERRED_FEATURE_TEST` | PR-B macro 4x4 pause; permanent skip until child-pool fixture |
| `tests/unit/asteroid_lab/test_rttp_reconstruction_fixture_e2e.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_replay_diagnostics.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_replay_parity.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_replay_sink.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_route_goals.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_selection_fot_prefilter.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_skeleton.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_solver_summary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_throughput_policy_diagnostic.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_transport_kind_route_domain.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_rttp_v02_track_expectations.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_run_solver_management_command.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_runtime_gene_template_source.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_solver_run_lab_summary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_solver_runtime_entry.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_solver_runtime_entry_catalog_summary.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_solver_runtime_entry_t2_policy_slug.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_throughput_shortfall.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_throughput_target.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_timeline_composer.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_topology_service.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_trace_logging.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |
| `tests/unit/asteroid_lab/test_validation_readonly_guards.py` | `PROTECTED_CONTRACT` | Asteroid lab domain contract (default protect in F0) |

### `unit/config` (1 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/config/test_shapez_runtime_flags.py` | `PROTECTED_CONTRACT` | Top-level unit contract gate |

### `unit/game_data` (26 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/game_data/test_admin_browse.py` | `ENV_GUARD_SKIP` | Conditional pytest.skip when pinned dump / seed missing |
| `tests/unit/game_data/test_building_assembly_audit.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_connectable_signatures.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_cross_references.py` | `ENV_GUARD_SKIP` | Conditional pytest.skip when pinned dump / seed missing |
| `tests/unit/game_data/test_domain_coverage_manifest.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_import_guards.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_import_metadata_unification.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_lazy_localized_text.py` | `ENV_GUARD_SKIP` | Conditional pytest.skip when pinned dump / seed missing |
| `tests/unit/game_data/test_mining_extraction_rules.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_models.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_no_raw_json_domain_storage.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_seed_game_data_taxonomy.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_shape_recipe_provenance.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_simulation_clr_parser.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_simulation_parameter_registry.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_simulation_path_coverage.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_simulation_speed_import.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_simulation_systems_import.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_snapshot_builder.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_snapshot_selectors.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_source_object_coverage.py` | `ENV_GUARD_SKIP` | Conditional pytest.skip when pinned dump / seed missing |
| `tests/unit/game_data/test_speed_dump_shapes.py` | `ENV_GUARD_SKIP` | Conditional pytest.skip when pinned dump / seed missing |
| `tests/unit/game_data/test_stratified_sample.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_toolbar_closure.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_toolbar_identity.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |
| `tests/unit/game_data/test_toolbar_tree.py` | `PROTECTED_CONTRACT` | game_data import / catalog / provenance contracts |

### `unit/shapez_core` (10 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/shapez_core/test_admin_identifier_sprite.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_backfill_sprite_static_relpaths.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_basedata_ivvd.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_crystal_geometry.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_ivvd_lookup_fixture.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_lab_sprite_identifier_service.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_lab_sprite_path.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_shape_code_parser.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_shape_render_scene.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_core/test_shapez_copy_decode.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |

### `unit/shapez_solver` (20 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/shapez_solver/test_color_mix_semantics.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_fluid_carrier_render_scene.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_graph_document_primitive_chain.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_macro_recipe_graph_visual.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_models.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_operation_catalog.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_operation_engine.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_operation_semantics_crystal.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_pattern_classifier.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_pattern_lab_service.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_preview_scene_payload_equivalence.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_connection_rule_fixture_alignment.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_cost_hints.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_input_carrier.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_react_flow_adapter.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_recipe_validation.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_recompute.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_source_carrier.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_recipe_graph_topology.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |
| `tests/unit/shapez_solver/test_serialize_graph_node_sync_png.py` | `PROTECTED_CONTRACT` | Recipe graph / shape core public contracts |

### `unit/test_build_locale_ko_strict.py` (1 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/test_build_locale_ko_strict.py` | `PROTECTED_CONTRACT` | Top-level unit contract gate |

### `unit/web` (9 files)

| path | grade | reason |
|------|-------|--------|
| `tests/unit/web/test_asteroid_game_data_snapshot.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_asteroid_lab_page_context.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_asteroid_run_solver_config.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_editor_graph_layout.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_graph_preview.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_replay_frame_cell_lookup.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_shape_part_sprite.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_solver_graph_layout.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |
| `tests/unit/web/test_solver_graph_markup.py` | `PROTECTED_CONTRACT` | Lab template / page context / replay JS contracts |


---

## Promotion log

| Date | PR | Action |
|------|-----|--------|
| 2026-05-30 | F0 | Full inventory synced to registry (240 files) |
| — | F1+ | Record promotions to `PR_F_APPROVED_DELETIONS` |
