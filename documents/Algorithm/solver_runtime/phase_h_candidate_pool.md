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

# Phase H ??Candidate Pool Build / Dedupe / Truncate

## ëª©ì 

geometry + route probeë¥??µê³¼??attemptë§?**normal candidate**ë¡?ë§Œë“ ??

## ?…ë ¥

```text
GeometryValidationResult (pass)
RouteProbeResult (reachable)
ProjectedGenePlacement
```

## ?°ì¶œë¬?

```text
CandidatePool (normal + rejected)
```

## ?‘ì—…

### Normal candidate ì¡°ê±´

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

?™ì¼ `CandidateEquivalenceKey`??**route_probe ?´ì „**??`candidate_id` ìµœì†Ÿê°??¹ìë§?probe?œë‹¤.  
probe ??`dedupe_gene_candidates`??truncate ??**2ì°??ˆì „ë§?*?´ë‹¤.

### Truncate

`max_candidates`ê°€ ?ˆìœ¼ë©?dedupe ??

```text
base_score desc
route_probe_result.cost asc
candidate_id asc
```

## ê¸ˆì?

- placement commit
- unreachable??normal pool???¬í•¨ ([Â§0.4](00_core_principles.md))
- server coord ?´ì™¸ ì¢Œí‘œ

## ?„ë£Œ ì¡°ê±´

- [x] normal/rejected ë¶„ë¦¬ deterministic
- [x] dedupe ??truncate ?œì„œ ê³ ì •
- [x] generatorê°€ layout??ë³€ê²½í•˜ì§€ ?ŠìŒ

## ?„ìˆ˜ ?ŒìŠ¤??

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

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- êµ¬í˜„: `candidate_dtos.py` (`GeneCandidate`), `candidate_equivalence.py`, `candidate_generator.py`
- ?ˆê±°??RESEARCH??`BundleCandidate` ëª…ì¹­?€ ?¬ìš©?˜ì? ?ŠìŒ
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md)

## ?¤ìŒ Phase

??[`phase_i_candidate_selection.md`](phase_i_candidate_selection.md)
