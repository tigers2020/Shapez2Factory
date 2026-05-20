---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: B
pr: 1B
related_docs:
  - documents/Algorithm/solver_runtime/00_core_principles.md
  - documents/Algorithm/asteroid_lab_01_optimization_input.md
---

# Phase B — Build OptimizationInput

## 목적

reconstruction snapshot을 optimization layer의 정본 DTO로 변환한다. §0.3 extension kind → field kind 정규화는 **본 adapter 경계**에서 수행한다.

## 입력

```text
LoadedReconstructionSnapshot
```

## 산출물

```python
OptimizationInput(
    asteroid_cells=...,
    mineable_cells=...,
    rim_cells=...,
    interior_cells=...,
    external_void_cells=...,
    route_goals=...,              # seed only — see below
    existing_transport_cells=...,
    existing_trunk_cells=...,
    protected_corridor_cells=...,
    blocked_cells=...,
    topology_graph=...,
    asteroid_bbox=...,
    route_domain_bbox=...,
    bbox=...,  # deprecated alias == route_domain_bbox
)
```

### Dual bbox (Phase B adapter)

| Field | Meaning |
|-------|---------|
| `asteroid_bbox` | Tight inclusive bbox over `mineable_cells` (fallback: all decoded server coords if empty) |
| `route_domain_bbox` | `expand_bbox(asteroid_bbox, OUTER_VOID_PADDING)` with `OUTER_VOID_PADDING = 10` |
| `bbox` | Legacy alias; must equal `route_domain_bbox` |

`external_void_cells` = all coords in `route_domain_bbox` that are **not** occupied decoded cells (`all_sv`). Reconstruction topology compare bbox stays tight (see `topology_contract`); only optimization routing expands.

### `route_goals` 경계 (Phase B vs C)

| Phase | `route_goals` 역할 |
|-------|-------------------|
| **B** | **seed / basic only** — 비어 있거나(`frozenset()`), 기존 trunk·transport에서 추출한 최소 goal. **planned set 완성 책임 없음.** |
| **C** | **planned `RouteGoal` 정본** — capacity planner·external margin/void 선택으로 생성·보강. PR2 probe·PR3+는 **C 이후** goal 집합 사용. |

Phase B 완료 조건에 “모든 external margin goal이 채워짐”을 **넣지 않는다.**

## 작업

1. extractor / miner / extension 제거 좌표 → asteroid evidence → `asteroid_cells` + `mineable_cells`
2. `asteroid_shape_field` / `asteroid_fluid_field` → 둘 다 mineable asteroid field
3. belt / pipe 제거 좌표 → asteroid evidence 아님 → `existing_transport_cells` 또는 route domain evidence
4. `shapeMinerExtension` / `fluidMinerExtension` 등 → field kind 정규화 ([`00_core_principles.md`](00_core_principles.md) §0.3)
5. 모든 coord를 Server X/Y로 확정
6. `asteroid_bbox` / `route_domain_bbox` 분리 및 padded `external_void_cells` 생성 (`reconstruction_adapter`)

## 금지

- optimizer·candidate_geometry·route_probe 내부에서 cell.kind로 mineable 판정
- optimization 내부 raw↔server 재변환
- DB 원본 수정

## 완료 조건

- [ ] all coords are Server X/Y
- [ ] mineable field kind does not depend on strict fluid kind in optimizer
- [ ] extension/miner evidence is represented as mineable asteroid field sets
- [ ] `RouteDomainSnapshotBuilder` 단일 진입으로 `route_domain` 시드 가능
- [ ] `route_goals`는 empty 또는 seed만 — planned goal은 Phase C 책임

## 필수 테스트

PR1B — `tests/unit/asteroid_lab/test_optimization_input.py` (DTO·adapter·좌표) — [`implementation_sequence.md`](implementation_sequence.md).

## 관련 코드·문서

- [`asteroid_lab_01_optimization_input.md`](../asteroid_lab_01_optimization_input.md)
- `django_apps/asteroid_lab/optimization/` — `OptimizationInput` DTO
- **PR1B 부분 완료:** `reconstruction_adapter.optimization_input_from_reconstruction`, `route_domain.py` ([`implementation_sequence.md`](implementation_sequence.md))
- **패키지 정본:** `asteroid_lab/optimization` only — `shapez_asteroid` 제거됨 ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §2)

## 다음 Phase

→ [`phase_c_capacity_route_goals.md`](phase_c_capacity_route_goals.md)
