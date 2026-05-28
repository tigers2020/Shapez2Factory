---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: H
pr: 3
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_03_candidate_generator.md
---

# Phase H ? Candidate Pool Build / Dedupe / Truncate

## Purpose

Turn attempts that pass geometry + route probe into **normal candidates**.

## Input

```text
GeometryValidationResult (pass)
RouteProbeResult (reachable)
ProjectedGenePlacement
```

## Output

```text
CandidatePool (normal + rejected)
```

## Tasks

### Normal candidate conditions

```text
geometry valid
route_probe_result.reachable is True
route_probe_result.reached_goal is not None
```

### Rejected candidate

```text
geometry failure
route_probe unreachable
budget exceeded
no goal cells
```

### Candidate ID

```text
{gene_id}:{anchor_x},{anchor_y}:{rotation}:{transport_kind}
```

### Equivalence key

```text
occupied_cells
route_probe_start
output_dir
transport_kind
base_throughput
topology_signature
```

### Dedupe

For same `CandidateEquivalenceKey`, **before route_probe** keep smallest `candidate_id` lexicographically.  
After probe, `dedupe_gene_candidates` runs **again before** truncate.

### Truncate

When `max_candidates` is set, after dedupe:

```text
base_score desc
route_probe_result.cost asc
candidate_id asc
```

## Forbidden

- placement commit
- unreachable in normal pool ([§0.4](00_core_principles.md))
- coordinates outside server coord

## Completion criteria

- [x] normal/rejected split deterministic
- [x] dedupe then truncate order fixed
- [x] generator does not modify layout

## Required tests

```text
test_candidate_generator_reachable_only_enters_normal_pool
test_candidate_generator_rejects_unreachable
test_candidate_generator_dedupes_before_max_candidates
test_candidate_generator_does_not_commit_placements
test_candidate_generator_uses_island_coords_only
test_candidate_id_is_deterministic
test_dedupe_skips_duplicate_route_probe
test_candidate_generator_exposes_timing
```

## Related code?documents

- Implementation: `candidate_dtos.py` (`GeneCandidate`), `candidate_equivalence.py`, `candidate_generator.py`
- Legacy RESEARCH `BundleCandidate` naming not used
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md)

## Next Phase

? [`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)
