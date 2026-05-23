---
status: ARCHIVED
archived_reason: Solver optimization pipeline removed 2026-05-22
superseded_by: docs/superpowers/specs/2026-05-22-strip-solver-keep-recon-complete-design.md
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: D
pr: 1 (?„ë£Œ)
related_docs:
  - documents/Algorithm/asteroid_lab_02_pattern_library.md
  - documents/Algorithm/solver_runtime/phase_e_gene_projection.md
---

# Phase D ??Load GeneTemplate Library

## ëª©ì 

GeneTemplate loaderë¡??˜í”Œ ? ì „???¼ì´ë¸ŒëŸ¬ë¦¬ë? ë¡œë“œ?œë‹¤. PR1?ì„œ êµ¬í˜„ ?„ë£Œ.

## ?…ë ¥

```text
JSON fixtures (tests/fixtures/asteroid_lab/gene_templates/)
GeneratedSampleGene parser
DB thin adapter ???„ì†
```

## ?°ì¶œë¬?

```python
tuple[GeneTemplate, ...]
```

## ê³„ì•½

```text
canonical output direction = E
fixed_output_transport_offset = (1, 0)
route_probe_start_offset = (2, 0)
occupied_offsets = extractor + extensions only
```

`fixed_output_transport` = extractor ì¶œë ¥ ì§í›„ ?„ìˆ˜ ì²?belt/pipe ?€.  
`route_probe_start` = ê·??¤ìŒ route search ?œì‘??([`open_decisions.md`](open_decisions.md) OD-1).

## ?‘ì—…

1. JSON fixture ?ëŠ” `GeneratedSampleGene`?ì„œ `GeneTemplate` ?Œì‹±
2. canonical E (`output_dir=E`) ê²€ì¦?
3. offset ì§‘í•©Â·throughput_factor ê³„ì•½ ? ì?

## ê¸ˆì?

- occupied??`fixed_output_transport` / `route_probe_start` ?¬í•¨
- non-canonical E ?œí”Œë¦¿ì„ optimizer??ì§ì ‘ ?¬ì… (loaderê°€ ê±°ë?)

## ?„ë£Œ ì¡°ê±´

- [x] `GeneTemplate` DTOÂ·loaderÂ·fixture tests green (PR1)
- [x] `gene_projection`??canonical E ?„ì œ
- [ ] DB adapter (?„ì† PR)

## ?„ìˆ˜ ?ŒìŠ¤??

```text
tests/unit/asteroid_lab/test_gene_template_loader.py
tests/unit/asteroid_lab/test_gene_projection.py
```

## ê´€??ì½”ë“œÂ·ë¬¸ì„œ

- `django_apps/asteroid_lab/optimization/gene_template.py`
- `django_apps/asteroid_lab/optimization/gene_template_loader.py`
- `django_apps/asteroid_lab/optimization/gene_projection.py`
- `django_apps/asteroid_lab/optimization/coord_transform.py`
- ?ˆê±°???¨í„´ ?œìˆ : [`asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) (`BundlePattern` ??êµ¬í˜„?€ `GeneTemplate`)

## ?¤ìŒ Phase

??[`phase_e_gene_projection.md`](phase_e_gene_projection.md)
