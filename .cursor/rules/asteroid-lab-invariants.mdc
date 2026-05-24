---

description: "Asteroid Lab coordinate·replay·DTO·export·solver invariants (MUST when working on globs)"

globs:

  - django_apps/asteroid_lab/**

  - django_apps/shapez_asteroid/**

  - tests/unit/asteroid_lab/**

  - tests/unit/shapez_asteroid/**

  - documents/Algorithm/asteroid_lab*.md

alwaysApply: false

---

# Asteroid Lab invariants (MUST)



Chat output follows [shapez2-core.mdc](mdc:.cursor/rules/shapez2-core.mdc) Caveman §6. **Violations and suspected violations** must be recorded under **## Risks** with the `invariant:` prefix.



TDD · test-protected items table: [testing.md § Domain invariants](mdc:documents/ai/manuals/testing.md#domain-invariants-that-must-be-test-protected).



| Topic | MUST | Test / doc anchor |

|------|------|-------------------|

| **Coordinates** | Copy JSON `X`/`Y` = **island-local** (omitted→0; `X==0` valid). Persist/fingerprint: `island_bbox_left_bottom_raw_xy_v1` / `island_raw_xy_v1` (PR-F). RTTP solver default `CoordFrame.ISLAND_RAW`. **Forbidden:** dense server `(server_x`,`server_y`)·`server_coords` bridge·persist attach. World map: no `x==0` column. AST: `test_coordinate_frame_ast_gate`. Lab UI: island `x`/`y` only. | [`research_shapez2_copy_json_island_local_coords_2026-05-23.md`](mdc:documents/research/research_shapez2_copy_json_island_local_coords_2026-05-23.md); [`2026-05-23-coordinate-tagged-frames-design.md`](mdc:docs/superpowers/specs/2026-05-23-coordinate-tagged-frames-design.md) |

| **Replay** | On schema · append semantics change: version · doc. **No payload semantic substitution.** metrics/NDJSON/artifact **not algorithm input.** **Single replay timeline**; all frames 2D `map_view`. | [`asteroid_lab_09_replay_timeline`](mdc:documents/Algorithm/asteroid_lab_09_replay_timeline.md); `test_manual_snapshot_replay_not_used_as_algorithm_input_doc` |

| **DTO·fingerprint** | `coord_system` required. Layout map v2 = island bbox-normalized; absolute v2 = island raw x/y. | [`layout_fingerprint.py`](mdc:django_apps/asteroid_lab/snapshots/layout_fingerprint.py) |

| **Export** | dense anchor export; [`sample_gene_exhaustive_generator`](mdc:django_apps/asteroid_lab/services/sample_gene_exhaustive_generator.py) NWS batches change **export layer only**. | [`official_blueprint_canonical_export`](mdc:documents/ai/plans/official_blueprint_canonical_export.md) |

| **Candidate** | No placement **commit**. Generate → local geometry → immediate route probe → reachable only in normal pool. | [`asteroid_lab_03`](mdc:documents/Algorithm/asteroid_lab_03_candidate_generator.md) |

| **Commit** | commit-time **latest `route_domain` re-probe**. `RouteDomainSnapshotBuilder.build_snapshot` is **canonical**; no separate `build_commit_snapshot` semantics. candidate reachable ≠ final proof. | [`asteroid_lab_07`](mdc:documents/Algorithm/asteroid_lab_07_incremental_commit.md); `test_incremental_commit_reprobes_latest_domain` |
| **Fitness vs survivability** | `FitnessBreakdown` penalties = **predictive** (candidate probe). `CommitSurvivabilityMetrics` = **observed** — solver/GA/replay→input **forbidden**. | [`asteroid_lab_05`](mdc:documents/Algorithm/asteroid_lab_05_genome_fitness.md); [`asteroid_lab_10`](mdc:documents/Algorithm/asteroid_lab_10_development_sequence.md) §10B |
| **Replay truncation** | **Fixture envelope ≠ runtime persist.** Track `truncation_reason` from **last frame** `metrics`; top-level persist **forbidden**. | [`asteroid_lab_12`](mdc:documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md) §6.1; `test_build_lab_replay_truncation_surfaces_track_metrics` |
| **Evolution RNG** | `forced_distant_mutation` via **seed-stable hash** only; unseeded `random`/`uuid4` **forbidden**. v0: GA loop deferred. | [`asteroid_lab_06`](mdc:documents/Algorithm/asteroid_lab_06_evolutionary_search.md); `test_evolution_distant_mutation_slot_deterministic` |

| **Validation** | read-only assert; no route·placement·topology **repair**. | [`asteroid_lab_08`](mdc:documents/Algorithm/asteroid_lab_08_validation.md); [ADR-003](mdc:documents/adr/ADR-003-final-validation-assertion-gate.md) |

| **Lab replay timeline** | One product replay; global monotonic `frame_index`. **No second optimization controller** (goal). dual-track policy **retired**. | `asteroid_lab_09_replay_timeline`; `test_lab_js_replay_wiring_smoke` |

| **Enums** | `issue_code`·`event_type`·`failure_reason` etc. **StrEnum/const** — no free-form strings. | Phase DTO docs; `test_invalid_event_type_rejected` |

| **Docs** | CANON/ACTIVE distinction. Plan · [AGENTS.md](mdc:AGENTS.md) approval gate before meaningful implementation. | — |



## Canonical sources



- [`documents/Algorithm/asteroid_lab_01_optimization_input.md`](mdc:documents/Algorithm/asteroid_lab_01_optimization_input.md)

- [`documents/Algorithm/asteroid_lab_03_candidate_generator.md`](mdc:documents/Algorithm/asteroid_lab_03_candidate_generator.md)

- [`documents/Algorithm/asteroid_lab_07_incremental_commit.md`](mdc:documents/Algorithm/asteroid_lab_07_incremental_commit.md)

- [`documents/Algorithm/asteroid_lab_08_validation.md`](mdc:documents/Algorithm/asteroid_lab_08_validation.md)

- [`documents/Algorithm/asteroid_lab_09_replay_timeline.md`](mdc:documents/Algorithm/asteroid_lab_09_replay_timeline.md)

- [`documents/refactory/asteroid_server_coords_layout_fingerprint_2026-05-16.md`](mdc:documents/refactory/asteroid_server_coords_layout_fingerprint_2026-05-16.md)

- [`documents/ai/plans/official_blueprint_canonical_export.md`](mdc:documents/ai/plans/official_blueprint_canonical_export.md)


