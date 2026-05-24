---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: D
pr: 1 (complete)
related_docs:
  - documents/Algorithm/asteroid_lab_02_pattern_library.md
  - documents/Algorithm/solver_runtime/phase_e_gene_projection.md
---

# Phase D ? Load GeneTemplate Library

## Purpose

Load sample gene library via GeneTemplate loader. Implemented in PR1.

## Input

```text
JSON fixtures (tests/fixtures/asteroid_lab/gene_templates/)
GeneratedSampleGene parser
DB thin adapter ? future
```

## Output

```python
tuple[GeneTemplate, ...]
```

## Contract

```text
canonical output direction = E
fixed_output_transport_offset = (1, 0)
route_probe_start_offset = (2, 0)
occupied_offsets = extractor + extensions only
```

`fixed_output_transport` = first belt/pipe cell immediately after extractor output.  
`route_probe_start` = next route search start ([`open_decisions.md`](open_decisions.md) OD-1).

## Tasks

1. Parse `GeneTemplate` from JSON fixture or `GeneratedSampleGene`
2. Validate canonical E (`output_dir=E`)
3. Preserve offset set·throughput_factor contract

## Forbidden

- `fixed_output_transport` / `route_probe_start` included in occupied
- Non-canonical E templates fed directly to optimizer (loader rejects)

## Completion criteria

- [x] `GeneTemplate` DTO·loader·fixture tests green (PR1)
- [x] `gene_projection` enforces canonical E
- [ ] DB adapter (future PR)

## Prerequisite phase

```text
tests/unit/asteroid_lab/test_gene_template_loader.py
tests/unit/asteroid_lab/test_gene_projection.py
```

## Related code·documents

- `django_apps/asteroid_lab/optimization/gene_template.py`
- `django_apps/asteroid_lab/optimization/gene_template_loader.py`
- `django_apps/asteroid_lab/optimization/gene_projection.py`
- `django_apps/asteroid_lab/optimization/coord_transform.py`
- Legacy pattern docs: [`asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) (`BundlePattern` ? implementation is `GeneTemplate`)

## Next Phase

? [`phase_e_gene_projection.md`](phase_e_gene_projection.md)
