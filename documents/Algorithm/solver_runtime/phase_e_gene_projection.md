---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: E
pr: 2
related_docs:
  - documents/Algorithm/solver_runtime/phase_d_gene_templates.md
  - documents/Algorithm/solver_runtime/phase_f_geometry_validation.md
---

# Phase E — Project Genes to Candidate Attempts

## 목적

`GeneTemplate`을 rim anchor에 회전 투영하여 **시도(attempt)** 만 생성한다. layout commit이 아니다.

## 입력

```text
OptimizationInput
tuple[GeneTemplate, ...]
CandidateGenerationConfig
```

## 산출물

```text
ProjectedGenePlacement attempts
```

## 작업

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

- `project_gene_placement` — `django_apps/asteroid_lab/optimization/gene_projection.py` (PR1)
- 투영 결과: `occupied_cells`, `route_probe_start`, `fixed_output_transport`, `output_dir`, `transport_kind` 등

## 금지

- layout commit
- commit_order로 사용하는 enumeration
- rim 순회하며 extractor 즉시 설치 ([§0.1](00_core_principles.md))

**중요:** 이 루프는 **deterministic enumeration**이다.

## 완료 조건

- [ ] 동일 입력·설정에서 투영 순서·결과가 deterministic
- [ ] `ProjectedGenePlacement`가 server coord만 사용
- [ ] transport_kind가 config와 일치

## 필수 테스트

PR2 geometry/route 테스트 전제 — [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md), [`implementation_sequence.md`](implementation_sequence.md) § PR2.

## 관련 코드·문서

- `gene_projection.py`
- [`asteroid_lab_03_candidate_generator.md`](../asteroid_lab_03_candidate_generator.md) — rim-only 후보 철학

## 다음 Phase

→ [`phase_f_geometry_validation.md`](phase_f_geometry_validation.md)
