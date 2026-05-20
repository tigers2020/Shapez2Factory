---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: M
pr: 7
related_docs:
  - documents/Algorithm/asteroid_lab_09_replay_debug.md
  - documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md
  - documents/Algorithm/solver_runtime/01_entry_point.md
---

# Phase M — Persist / Replay / UI Payload

## 목적

solver 결과를 DB와 UI에 반영한다. Lab replay와 optimization replay는 **암묵 동기화하지 않는다.**

> **PR7 = 재구현 금지:** [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md) 의 persist/read/validation/HUD(12F–12L 등)를 **재작성하지 않는다.** Runtime Phase M 이벤트는 기존 writer/reader에 **thin adapter**로만 연결 ([`ARCHITECTURE_RECONCILIATION.md`](ARCHITECTURE_RECONCILIATION.md) §6).

## 입력

```text
ValidationResult
MaterializedLayoutCells
optimization run metrics
replay frames (accumulated)
```

## 산출물

```text
SolverRun.config_json (optimization_replay_frames, solver_summary, …)
UI: optimization replay track + layout preview
```

## 작업

### Persist (기존 경로 재사용)

```text
SolverRun.config_json          # 기존 Lab persist 계약
optimization_replay_frames     # 기존 frame list validator·truncation 정책 재사용
solver_summary
materialized_layout preview
validation_result
```

신규: Runtime orchestration → **기존** attach/read API 호출 + `OptimizationReplayEventType` (`django_apps/asteroid_lab/optimization/enums.py`) 중 Runtime 필수 subset 기록.

### Replay 필수 이벤트

```text
optimization.input_loaded
capacity.plan_created
route_goal.generated
pattern.generated
candidate.generated
candidate.rejected
route_probe.succeeded
route_probe.failed
candidate_pool.completed
candidate_selection.completed
route.commit_attempted
route.committed
route.rolled_back
route.materialized
validation.completed
```

`OptimizationReplayEventType` enum — algorithm input 금지.

### UI

```text
Lab replay = map rendering authority
Optimization replay = metadata / overlay observation
No implicit sync
```

## 금지

- replay·NDJSON를 solver/GA 입력으로 사용
- Lab timeline과 optimization frame index 암묵 동기화 ([`asteroid_lab_09`](../asteroid_lab_09_replay_debug.md) dual-track)

## 완료 조건

- [ ] persist 후 `solver_run_id`·replay payload 조회 가능
- [ ] 이벤트 순서 deterministic
- [ ] UI에 optimization track attach (Lab 페이로드 비변형)

## 필수 테스트

```text
test_solver_button_pipeline_persists_result
test_solver_button_pipeline_emits_replay_events
test_solver_button_pipeline_validation_read_only
test_solver_button_pipeline_no_implicit_lab_optimization_sync
```

## 관련 코드·문서

- [`django_apps/web/views/public_pages.py`](../../../django_apps/web/views/public_pages.py)
- [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md)
- [`asteroid_lab_13_replay_payload_scalability.md`](../asteroid_lab_13_replay_payload_scalability.md)

## 다음 Phase

없음 (파이프라인 종료). 진입: [`01_entry_point.md`](01_entry_point.md).
