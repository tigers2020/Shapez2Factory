---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: E
pr: 2
related_docs:
  - documents/Algorithm/solver_runtime/phase_d_gene_templates.md
  - documents/Algorithm/solver_runtime/phase_f_geometry_validation.md
---

# Phase E ??Project Genes to Candidate Attempts

## ëª©ì 

`GeneTemplate`??rim anchor???Œì „ ?¬ì˜?˜ì—¬ **?œë„(attempt)** ë§??ì„±?œë‹¤. layout commit???„ë‹ˆ??

## ?…ë ¥

```text
OptimizationInput
tuple[GeneTemplate, ...]
CandidateGenerationConfig
```

## ?°ì¶œë¬?

```text
ProjectedGenePlacement attempts
```

## ?‘ì—…

```python
for anchor in sorted(inp.rim_cells):
    for gene in sorted(gene_templates, key=lambda g: g.gene_id):
        for rotation in (N, E, S, W):
            for transport_kind in sorted(config.transport_kinds):
                projected = project_gene_placement(
                    anchor=anchor,
                    rotation=rotation,
                    gene=gene,
                )
```

- `project_gene_placement` ??`django_apps/asteroid_lab/optimization/gene_projection.py` (PR1)
- ?¬ì˜ ê²°ê³¼: `occupied_cells`, `route_probe_start`, `fixed_output_transport`, `output_dir`, `transport_kind` ??

## ê¸ˆì?

- layout commit
- commit_orderë¡??¬ìš©?˜ëŠ” enumeration
- rim ?œíšŒ?˜ë©° extractor ì¦‰ì‹œ ?¤ì¹˜ ([Â§0.1](00_core_principles.md))

**ì¤‘ìš”:** ??ë£¨í”„??**deterministic enumeration**?´ë‹¤.

## ?„ë£Œ ì¡°ê±´

- [ ] ?™ì¼ ?…ë ¥Â·?¤ì •?ì„œ ?¬ì˜ ?œì„œÂ·ê²°ê³¼ê°€ deterministic
- [ ] `ProjectedGenePlacement`ê°€ server coordë§??¬ìš©
- [ ] transport_kindê°€ config?€ ?¼ì¹˜

## ?„ìˆ˜ ?ŒìŠ¤??

PR2 geometry/route ?ŒìŠ¤???„ì œ ??[`phase_f_geometry_validation.md`](phase_f_geometry_validation.md), [`implementation_sequence.md`](implementation_sequence.md) Â§ PR2.

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- `gene_projection.py`
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) ??rim-only ?„ë³´ ì² í•™

## ?¤ìŒ Phase

??[`phase_f_geometry_validation.md`](phase_f_geometry_validation.md)
