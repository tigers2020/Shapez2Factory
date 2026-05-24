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

# Phase E ? Project Genes to Candidate Attempts

## Purpose

Project `GeneTemplate` to rim anchors?rotations to create **attempts**. Not layout commit.

## Input

```text
OptimizationInput
tuple[GeneTemplate, ...]
CandidateGenerationConfig
```

## Output

```text
ProjectedGenePlacement attempts
```

## Tasks

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

- `project_gene_placement` ? `django_apps/asteroid_lab/optimization/gene_projection.py` (PR1)
- Projection result: `occupied_cells`, `route_probe_start`, `fixed_output_transport`, `output_dir`, `transport_kind` etc.

## Forbidden

- layout commit
- Using commit_order for enumeration
- Installing extractor immediately while iterating rim ([§0.1](00_core_principles.md))

**Important:** This loop is **deterministic enumeration**.

## Completion criteria

- [ ] Same input?config produces deterministic projection order?results
- [ ] `ProjectedGenePlacement` uses server coords only
- [ ] transport_kind matches config

## Prerequisite phase

PR2 geometry/route phase ? see [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md), [`implementation_sequence.md`](implementation_sequence.md) § PR2.

## Related code?documents

- `gene_projection.py`
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) ? rim-only candidate philosophy

## Next Phase

? [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md)
