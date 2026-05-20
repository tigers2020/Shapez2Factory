---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: F
pr: 2
related_docs:
  - documents/Algorithm/solver_runtime/phase_g_route_probe.md
  - documents/Algorithm/solver_runtime/00_core_principles.md
---

# Phase F — Geometry Validation

## 목적

투영된 gene이 asteroid topology 위에서 물리적으로 가능한지 검사한다. **OptimizationInput을 변경하지 않는다.**

## 입력

```text
OptimizationInput
ProjectedGenePlacement
```

## 산출물

```text
GeometryValidationResult
```

## 작업

검사 항목:

```text
extractor ∈ rim_cells
extensions ⊆ mineable_cells
occupied_cells ⊆ asteroid_cells
route_probe_start ∉ occupied_cells
route_probe_start valid in bbox / route domain candidate area
self-overlap 없음
```

`mineable_cells` / `rim_cells` / `asteroid_cells` 집합만 사용 — cell.kind 직접 판정 금지 ([§0.3](00_core_principles.md)).

### Reject reason (enum)

```text
extractor_not_rim
extension_not_mineable
occupied_outside_asteroid
pattern_overlap_self
output_stub_inside_occupied      # legacy enum member — 의미 = route_probe_start inside occupied
output_stub_invalid_coord        # legacy enum member — 의미 = route_probe_start invalid coord
```

**신규 테스트명:** [`00_core_principles.md`](00_core_principles.md) §0.7 — `test_geometry_rejects_route_probe_start_*` only.

## 금지

- validation에서 placement/route 수정
- `OptimizationInput` mutation
- kind 문자열로 mineable 판정

## 완료 조건

- [ ] valid/invalid 케이스가 deterministic reject reason 반환
- [ ] geometry 단계가 route probe보다 먼저 실행
- [ ] 입력 DTO 불변

## 필수 테스트

```text
test_geometry_accepts_valid_projected_gene
test_geometry_rejects_extractor_not_rim
test_geometry_rejects_extension_not_mineable
test_geometry_rejects_occupied_outside_asteroid
test_geometry_rejects_route_probe_start_inside_occupied
test_geometry_rejects_route_probe_start_invalid_coord
test_geometry_does_not_mutate_optimization_input
```

## 관련 코드·문서

- 예정: `django_apps/asteroid_lab/optimization/candidate_geometry.py`
- `tests/unit/asteroid_lab/test_candidate_geometry.py` (예정)

## 다음 Phase

→ [`phase_g_route_probe.md`](phase_g_route_probe.md)
