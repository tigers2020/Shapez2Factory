---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: F
pr: 2
related_docs:
  - documents/Algorithm/solver_runtime/phase_g_route_probe.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase F ??Geometry Validation

## ëª©ì 

?¬ì˜??gene??asteroid topology ?„ì—??ë¬¼ë¦¬?ìœ¼ë¡?ê°€?¥í•œì§€ ê²€?¬í•œ?? **OptimizationInput??ë³€ê²½í•˜ì§€ ?ŠëŠ”??**

## ?…ë ¥

```text
OptimizationInput
ProjectedGenePlacement
```

## ?°ì¶œë¬?

```text
GeometryValidationResult
```

## ?‘ì—…

ê²€????ª©:

```text
extractor ??rim_cells
extensions ??mineable_cells
occupied_cells ??asteroid_cells
route_probe_start ??occupied_cells
route_probe_start valid in bbox / route domain candidate area
self-overlap ?†ìŒ
```

`mineable_cells` / `rim_cells` / `asteroid_cells` ì§‘í•©ë§??¬ìš© ??cell.kind ì§ì ‘ ?ì • ê¸ˆì? ([Â§0.3](00_core_principles.md)).

### Reject reason (enum)

```text
extractor_not_rim
extension_not_mineable
occupied_outside_asteroid
pattern_overlap_self
output_stub_inside_occupied      # legacy enum member ???˜ë? = route_probe_start inside occupied
output_stub_invalid_coord        # legacy enum member ???˜ë? = route_probe_start invalid coord
```

**? ê·œ ?ŒìŠ¤?¸ëª…:** [`00_core_principles.md`](00_core_principles.md) Â§0.7 ??`test_geometry_rejects_route_probe_start_*` only.

## ê¸ˆì?

- validation?ì„œ placement/route ?˜ì •
- `OptimizationInput` mutation
- kind ë¬¸ì?´ë¡œ mineable ?ì •

## ?„ë£Œ ì¡°ê±´

- [ ] valid/invalid ì¼€?´ìŠ¤ê°€ deterministic reject reason ë°˜í™˜
- [ ] geometry ?¨ê³„ê°€ route probeë³´ë‹¤ ë¨¼ì? ?¤í–‰
- [ ] ?…ë ¥ DTO ë¶ˆë?

## ?„ìˆ˜ ?ŒìŠ¤??

```text
test_geometry_accepts_valid_projected_gene
test_geometry_rejects_extractor_not_rim
test_geometry_rejects_extension_not_mineable
test_geometry_rejects_occupied_outside_asteroid
test_geometry_rejects_route_probe_start_inside_occupied
test_geometry_rejects_route_probe_start_invalid_coord
test_geometry_does_not_mutate_optimization_input
```

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- ?ˆì •: `django_apps/asteroid_lab/optimization/candidate_geometry.py`
- `tests/unit/asteroid_lab/test_candidate_geometry.py` (?ˆì •)

## ?¤ìŒ Phase

??[`phase_g_route_probe.md`](phase_g_route_probe.md)
