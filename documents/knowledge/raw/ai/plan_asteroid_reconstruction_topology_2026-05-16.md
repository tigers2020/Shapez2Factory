---
status: ACTIVE
owner: asteroid-lab
last_reviewed: 2026-05-16
supersedes: []
superseded_by: []
related_epics: []
---

# Asteroid Lab: topology-only reconstruction (canon)

## Purpose

After removing **buildings (transport · miner · extension)** from decoded map, fill empty cells as `asteroid_*_field` judged only by **connection to external void + conservative enclosure guard**, not as `internal_void`.

## Module boundaries

- **Preprocessing (cleanup)**: `django_apps/asteroid_lab/cleanup/` — strippable removal, **`wall_coords`** output (extensible as shared replay/solver input)
- **Topology reconstruction**: `django_apps/asteroid_lab/reconstruction/` — fill from `cleaned_cells` + `wall_coords` + `bbox_bounds` only (no snapshot DTO dependency)
- **Replay serialization**: `django_apps/asteroid_lab/replay/` — `deconstruction_frames` / `reconstruction_frames` + `snapshot_map_replay` orchestration

## `wall_coords` contract

- `wall_coords` is **flood-fill topology barrier** set, not “decoded asteroid tiles only”.
- **extractor / extension** coords removed in cleanup are included in `wall_coords`.
- **belt / pipe** coords stay on removal list (`ignored_transport`) only; **not added to `wall_coords`**.
- Walkable empty cells and `wall_coords` are separate: removed miner cells may be absent from map rows but are walls in flood.

## Data (reconstruction input)

- `cleaned_cells` + `wall_coords` + `bbox_bounds` (+ server coords · fingerprint: see [`../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md))
- **Fill kind (shape/fluid)**: MVP uses only remaining decoded `asteroid_*_field` and existing majority vote; do not derive fill from removed miner type (no `field_vote_hints`)

## Reconstruction steps (before · after flood)

1. `close_diagonal_leaks(wall_coords)` — Chebyshev (L∞) pinhole only: **evidence walls input only**; strict wall-bbox **interior** cells not sealed (preserve internal holes)
2. `barrier = wall_coords ∪ diagonal_closed`
3. `external_reachable` — **4-neighbor** flood from padded bbox border
4. `interior = walkable - external` → component fill — guard is **`passes_bbox_interior` only**
5. `stamp_islands_uniform` — final `asteroid_*_field`

- 1-cell void touching bbox margin flood (narrow external passage · separator included) is **external** — do not fill
- Only flood-unreachable void is **interior_patch** candidate

- topology graph / routing adjacency: **4-neighbor** (`neighbors4_server`) — separate from closing morphology

## Forbidden

- `internal_void` in final `full_map`
- filled-hole-only debug overlay
- replay log · summary · removal types as fill decision input
- **orthogonal 1-cell slit sealing** globally (`close_orthogonal_one_cell_slits` in pipeline)
- re-inject inferred shell / sealed slit / diagonal close results as fill candidates (morphology → interior union)
- reuse inferred shell · seal results as opposing solid in next morphology pass (recursive closure)

## Verification

- `tests/unit/asteroid_lab/test_reconstruction_topology.py`
- `tests/unit/asteroid_lab/test_reconstruction_regression_overclose.py` (fixture `regression_narrow_external_channels.txt`)
- `tests/unit/asteroid_lab/test_reconstruction_fixture_contract.py` — line-by-line Server X/Y topology `reconstruction_required_.txt` ↔ `reconstruction_complete_solved.txt` (solved decode-only)
- `test_replay_snapshot_contract.py`

## Confidence / acceptance (production)

- `django_apps/asteroid_lab/reconstruction/confidence.py` — `confirmed_cells`, `ambiguous_cells`, `confidence_score`, `quality_tier`
- Production pass: `ambiguous_ratio ≤ 0.05`, `confidence_score ≥ 0.95`, `reconstruction_acceptance_ok(result)` (`CONFIDENT_RECONSTRUCTION`)
- solved fixture is calibration (overlap report) only, not accuracy score — `test_reconstruction_canon_line_confidence_calibration`
