---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: D
pr: 1 (완료)
related_docs:
  - documents/Algorithm/asteroid_lab_02_pattern_library.md
  - documents/Algorithm/solver_runtime/phase_e_gene_projection.md
---

# Phase D — Load GeneTemplate Library

## 목적

GeneTemplate loader로 샘플 유전자 라이브러리를 로드한다. PR1에서 구현 완료.

## 입력

```text
JSON fixtures (tests/fixtures/asteroid_lab/gene_templates/)
GeneratedSampleGene parser
DB thin adapter — 후속
```

## 산출물

```python
tuple[GeneTemplate, ...]
```

## 계약

```text
canonical output direction = E
fixed_output_transport_offset = (1, 0)
route_probe_start_offset = (2, 0)
occupied_offsets = extractor + extensions only
```

`fixed_output_transport` = extractor 출력 직후 필수 첫 belt/pipe 셀.  
`route_probe_start` = 그 다음 route search 시작점 ([`open_decisions.md`](open_decisions.md) OD-1).

## 작업

1. JSON fixture 또는 `GeneratedSampleGene`에서 `GeneTemplate` 파싱
2. canonical E (`output_dir=E`) 검증
3. offset 집합·throughput_factor 계약 유지

## 금지

- occupied에 `fixed_output_transport` / `route_probe_start` 포함
- non-canonical E 템플릿을 optimizer에 직접 투입 (loader가 거부)

## 완료 조건

- [x] `GeneTemplate` DTO·loader·fixture tests green (PR1)
- [x] `gene_projection`이 canonical E 전제
- [ ] DB adapter (후속 PR)

## 필수 테스트

```text
tests/unit/asteroid_lab/test_gene_template_loader.py
tests/unit/asteroid_lab/test_gene_projection.py
```

## 관련 코드·문서

- `django_apps/asteroid_lab/optimization/gene_template.py`
- `django_apps/asteroid_lab/optimization/gene_template_loader.py`
- `django_apps/asteroid_lab/optimization/gene_projection.py`
- `django_apps/asteroid_lab/optimization/coord_transform.py`
- 레거시 패턴 서술: [`asteroid_lab_02_pattern_library.md`](../asteroid_lab_02_pattern_library.md) (`BundlePattern` — 구현은 `GeneTemplate`)

## 다음 Phase

→ [`phase_e_gene_projection.md`](phase_e_gene_projection.md)
