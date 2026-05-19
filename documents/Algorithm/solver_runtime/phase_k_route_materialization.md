---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: K
pr: 6
related_docs:
  - documents/Algorithm/solver_runtime/open_decisions.md
---

# Phase K — Route Network Materialization

## 목적

확정된 route reservations를 실제 belt/pipe sprite/layout 구조로 변환한다. **merger/splitter 변환은 본 단계에서만** 수행한다.

## 입력

```text
confirmed placements
confirmed route reservations
shared path graph
transport kind
flow direction observations
```

## 산출물

```text
MaterializedLayoutCells
```

## 작업

### 변환 규칙

```text
single path → straight / turn
multiple incoming same kind → merger / yMerger / triple merger
multiple outgoing same kind → splitter / ySplitter / triple splitter
vertical / lift variants — later
```

### OD-1 권장

materialization 시 reservation path **앞에** `fixed_output_transport` 셀을 prepend ([`open_decisions.md`](open_decisions.md)).

## 금지

- candidate placement 중 merger/splitter 변환
- void 선설치 transport ([§0.2](00_core_principles.md))
- shape belt / fluid pipe 동일 셀 공유

## 완료 조건

- [ ] straight/turn이 path topology와 일치
- [ ] shared path에 merger/splitter 선택 deterministic
- [ ] shape/fluid overlap reject

## 필수 테스트

```text
test_route_materializer_creates_straight_and_turns
test_route_materializer_merges_same_kind_shared_paths
test_route_materializer_rejects_shape_fluid_overlap
test_route_materializer_selects_y_or_triple_merger
```

## 관련 코드·문서

- 예정: `route_network_materializer.py`

## 다음 Phase

→ [`phase_l_final_validation.md`](phase_l_final_validation.md)
