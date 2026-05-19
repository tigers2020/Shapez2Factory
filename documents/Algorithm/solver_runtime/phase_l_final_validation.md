---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: L
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_08_validation.md
  - documents/adr/ADR-003-final-validation-assertion-gate.md
---

# Phase L — Final Validation

## 목적

최종 layout이 solver contract를 만족하는지 **read-only**로 검증한다.

## 입력

```text
MaterializedLayoutCells
confirmed placements
RouteReservation(s)
OptimizationInput (final)
```

## 산출물

```python
ValidationResult(
    passed=True/False,
    issues=...,
)
```

## 작업

검증 항목:

```text
all extractor outputs connected
all route reservations reach valid RouteGoal
no orphan transport
no invalid overlap
transport kind consistency
reserved_cells match path
confirmed candidate has exactly one confirmed reservation
capacity violation 없음
```

`ValidationIssueCode` 등 **enum**만 사용 — 자유 문자열 금지.

## 금지

Validation은 다음을 하지 않는다:

```text
new route 생성
placement 수정
topology 수정
```

## 완료 조건

- [x] `passed=False` 시 `issues`에 구조화된 코드만
- [x] validation이 layout/route/topology를 변경하지 않음
- [x] confirmed ↔ 단일 CONFIRMED reservation 일치

## 필수 테스트

PR7 — `test_solver_button_pipeline_validation_read_only` ([`implementation_sequence.md`](implementation_sequence.md)).

## 관련 코드·문서

- [`asteroid_lab_08_validation.md`](../asteroid_lab_08_validation.md)
- ADR-003 (validation gate)

## 다음 Phase

→ [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md)
