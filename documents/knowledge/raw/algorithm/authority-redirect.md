# Asteroid Lab algorithm authority redirect

**Purpose:** Route stale `documents/Algorithm/` links to current authority.  
**Status:** `ACTIVE` ledger (raw index — not implementation canon).  
**Do not** treat deleted `documents/Algorithm/asteroid_lab_*.md` as authority.

## Current authority (use these)

| Topic | Authority | Notes |
|---|---|---|
| Algorithm execution queue (post-sequence) | [`asteroid_lab_11_future_execution_plan_post_sequence.md`](asteroid_lab_11_future_execution_plan_post_sequence.md) | Only `ACTIVE` file in this tree per [`README.md`](README.md) |
| Solver layers L2–L5 | Wiki [[asteroid-lab-algorithm]] | Synthesis; code in `src/shapez2_factory/application/asteroid_lab/layers/` |
| Coordinate frames (copy / island / world) | Wiki [[island-mechanics]]; code `copy_json_coords.py` | Supersedes slice `asteroid_lab_01` for coords |
| Gene canonical E → island grid | [`../domain-docs/asteroid_coord_transform_spec.md`](../domain-docs/asteroid_coord_transform_spec.md) | Raw domain contract; wiki defers to island-mechanics for copy JSON |
| Replay wire typing | Wiki [[asteroid-lab-wire-typing]]; `documents/ai/manuals/typing_contracts.md` | TypedDict + frozen dataclass split |
| CLI artifact + replay_core | `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` | BA-1…8 manifest contract |
| Term map (canonical / alias / ambiguous) | [`docs/ubiquitous-language.md`](../../../../docs/ubiquitous-language.md) | Agent glossary with evidence |
| Invariants (router) | `.cursor/rules/asteroid-lab-invariants.mdc` | **Stale refs inside** — see redirect table below |

## Redirect: former `documents/Algorithm/asteroid_lab_*.md`

| Former path (missing locally) | Redirect to |
|---|---|
| `asteroid_lab_01_optimization_input.md` | [[island-mechanics]] + `OptimizationInput` normalize in code; raw [`asteroid_coord_transform_spec.md`](../domain-docs/asteroid_coord_transform_spec.md) |
| `asteroid_lab_02_pattern_library.md` | `django_apps/asteroid_lab/genetic_sample/`; raw [`../game-rules/shapez2_asteroid_space_transport_throughput.md`](../game-rules/shapez2_asteroid_space_transport_throughput.md) |
| `asteroid_lab_03_candidate_generator.md` | `RouteDomainSnapshotBuilder` + `candidate_gen.py`; glossary **Candidate** |
| `asteroid_lab_05_genome_fitness.md` | Invariants router; glossary **Fitness** |
| `asteroid_lab_07_incremental_commit.md` | `RouteDomainSnapshotBuilder` + `commit_reprobe.py`; glossary **Commit** |
| `asteroid_lab_08_validation.md` | Invariants router; ADR-003 |
| `asteroid_lab_09_replay_timeline.md` | Artifact spec §3; `timeline_dtos.py`; glossary **frame_index** |
| `asteroid_lab_09_replay_debug.md` | Cross-ref only in `asteroid_lab_11` (instrumentation sequences) |
| `asteroid_lab_10_development_sequence.md` | Historical; raw [`../ai/plans/asteroid_lab_optimization_sequence_1a_1b.md`](../ai/plans/asteroid_lab_optimization_sequence_1a_1b.md) (plan, not canon) |
| `asteroid_lab_12_runtime_replay_wiring.md` | CLI-first spec + `artifact_replay_viewer_compose.py` |
| `asteroid_lab_13_replay_payload_scalability.md` | `lab_replay_lazy_handle.py`; env in `documents/ai/manuals/environment.md` |
| `mining_solver_cursor_sessions/*` | **Archived** — refactory memos only; not implementation authority |

## Related raw (not moved — ledger only)

| Raw path | Role |
|---|---|
| [`../domain-docs/asteroid_coord_transform_spec.md`](../domain-docs/asteroid_coord_transform_spec.md) | Gene E → island grid contract |
| [`../domain-docs/asteroid_game_data_snapshot.md`](../domain-docs/asteroid_game_data_snapshot.md) | Game data snapshot boundary |
| [`../game-rules/shapez2_asteroid_space_transport_throughput.md`](../game-rules/shapez2_asteroid_space_transport_throughput.md) | Throughput rates (also in game_rules canon) |
| [`../ai/plans/asteroid_lab_optimization_sequence_1a_1b.md`](../ai/plans/asteroid_lab_optimization_sequence_1a_1b.md) | Scoped plan; links to deleted Algorithm paths |
| [`../index/document_inventory.md`](../index/document_inventory.md) | **Stale** Algorithm rows — use this redirect + wiki [[algorithm-doc-authority]] |

## Policy

- **Do not modify** existing raw bodies to chase redirects (llm-wiki: raw is recoverable).
- New links should target wiki concepts, `docs/` specs, code modules, or this ledger.
- GitHub `master` may still host old `documents/Algorithm/` for archaeology — local repo does not.
