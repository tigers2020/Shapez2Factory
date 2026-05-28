---
status: AUDIT
owner: asteroid-lab
last_reviewed: 2026-05-22
language: en
related_docs:
  - asteroid_lab_mining_installation/00_source_of_truth.md
  - docs/superpowers/specs/2026-05-22-asteroid-miner-extension-reconcile-design.md
---

# Rule Contradiction Table — Miner, Extension, Installation

9-column table. PR-0 seed + PR-1 `03` reflects layers A/B. Aligned with PR-2 `04` narrative; only `needs-review` (throughput) remains for the program.

## Column definitions

| Column | Meaning |
|----|------|
| `topic` | Rule name |
| `legacy_claim` | Claim in legacy documents |
| `normalized_db_evidence` | Layer A — ORM/dump tables and rows |
| `reflected_db_evidence` | Layer B — simulation/reflection paths |
| `code_invariant` | Layer C — code symbols |
| `test_evidence` | Layer D — pytest / enum |
| `confidence` | `high` / `medium` / `low` |
| `verdict` | `keep` / `rewrite` / `clarify` / `delete` / `needs-review` |
| `action` | Target file/PR; for `needs-review` include **owner** and **gap** |

## Seed rows (PR-0)

| topic | legacy_claim | normalized_db_evidence | reflected_db_evidence | code_invariant | test_evidence | confidence | verdict | action |
|-------|--------------|------------------------|----------------------|----------------|---------------|------------|---------|--------|
| Extension max 0..3 | `asteroid_lab_02`: linear 0–3 extension | `03`: `ExtractorDefaultInternalVariant`, `PumpDefaultInternalVariant` + toolbar miner groups; blueprint `Layout_*` ≠ variant table | `03`: `ShapeMinerExtensionPlacementHelper`, `FluidMinerExtensionPlacementHelper`, `*ExtensionMetadata` | `throughput_factor_for_extension_count()` rejects >3; `GeneTemplate` occupied = extractor + extensions | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count`; `tests/unit/asteroid_lab/test_sample_gene_exhaustive.py::test_exhaustive_generator_extension_count_0_to_3` | high (C+D); medium (A Layout vs DB) | keep | `03` § Blueprint vs DB; `04` §1·§3 |
| Throughput 4/8/12/16 | `game_rules` CANON: base ×4, +×4 per extension, max ×16 | `03`: no rate column on `buildingvariant`; 2 internal variants in A | `03`: `unknownproperty` miner metadata; `simulationsystem` path TBD | `VALID_THROUGHPUT_FACTORS = {4,8,12,16}`; `throughput_factor_for_extension_count()` (`gene_template.py`) | `tests/unit/asteroid_lab/test_gene_template_loader.py::test_gene_template_throughput_factor_matches_extension_count` | medium | needs-review | **owner:** asteroid-lab · **gap:** simulation_systems rate path → scalar import · **next:** game_data phase import or deep path audit |
| rim-only | `asteroid_lab_03`: `RIM_ONLY` / rim-only reads like install order | `03`: rim is topology-derived (`rim_cells`), not a DB table | — | `ExtractorPlacementPolicy.RIM_ONLY` (`candidate_dtos.py`); `candidate_generator.py` default — **anchor ∈ rim_cells**, not greedy install | `tests/unit/asteroid_lab/test_candidate_generator.py::test_candidate_generator_does_not_commit_placements`; `::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | clarify | `04` §Key distinction·§3; **gap:** `asteroid_lab_03` RESEARCH body · owner: asteroid-lab |
| Candidate route probe | Phase 3 / overview: full-pool probe | — | — | `BundleCandidate.route_probe_result` at generation time; **not commit proof** | `tests/unit/asteroid_lab/test_candidate_generator.py::test_candidate_generator_reachable_only_enters_normal_pool` | high (C+D) | clarify | `04` §3–5; link `asteroid_lab_04_route_probe.md` |
| Commit-time reprobe | `asteroid_lab_07`: reprobe with latest `route_domain` | — | — | `RouteDomainSnapshotBuilder.build_snapshot` on each commit; candidate probe is reference only | `tests/unit/asteroid_lab/test_incremental_commit.py::test_incremental_commit_reprobes_latest_domain` | high | keep | strong-canon; `04` §5; keep `asteroid_lab_07` |
| Replay event vocabulary | UI / lab JS — no doc mapping | — | — | `ReplayEventType` (`replay_enums.py`): `candidate.generated`, `route_probe.succeeded`, `route.committed`, etc. | `tests/unit/asteroid_lab/test_replay_timeline_dto.py`; `tests/unit/asteroid_lab/test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` (input prohibition only) | medium | clarify | `04` §6 phase/event table; **gap:** JS per-control labels · owner: asteroid-lab |
| Replay algorithm input prohibition | `asteroid_lab_00` / invariants | — | — | metrics/NDJSON/replay frames excluded from optimization input | `tests/unit/asteroid_lab/test_cell_snapshot_service.py::test_manual_snapshot_replay_not_used_as_algorithm_input_doc` | high | keep | `asteroid_lab_09_replay_timeline.md` (ACTIVE); `asteroid_lab_12_runtime_replay_wiring.md`; **`09_replay_debug` is ARCHIVED** |

## Hub closing checklist

- [x] Every `needs-review` row has owner + evidence gap + next PR
- [x] Final `verdict` does not use 「not in DB」
- [x] `00`–`04` and `README` exist (`03` DB xref, `04` installation guide included)
- [x] `01`·`03`·`04` core claims aligned (candidate ≠ confirmed install)
- [ ] Resolve throughput `needs-review` (simulation rate path or import)
- [x] `02` action column reflects PR-1/PR-2 complete/partial (2026-05-22)
