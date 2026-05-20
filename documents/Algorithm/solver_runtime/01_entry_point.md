---
status: ACTIVE
owner: solver-runtime-pipeline
last_reviewed: 2026-05-19
phase: Entry
pr: 8
related_docs:
  - documents/Algorithm/solver_runtime/README.md
  - django_apps/web/views/public_pages.py
---

# Solver Button Entry Point

## 목적

사용자 UI에서 `Run Solver` 또는 `Solver` 버튼 클릭 시 백엔드 파이프라인을 시작한다. Phase A부터 M까지의 오케스트레이션 진입점을 정의한다.

## 트리거

사용자 UI: `Run Solver` / `Solver` 버튼 클릭.

## 백엔드 진입

```text
POST /asteroid-miner-layout/p/<slug>/run-solver/
```

- URL name: `web:asteroid-miner-layout-project-run-solver`
- 뷰: `asteroid_miner_layout_project_run_solver` ([`public_pages.py`](../../../django_apps/web/views/public_pages.py))
- 서비스: `run_solver_runtime_for_project` ([`solver_runtime_entry.py`](../../../django_apps/asteroid_lab/services/solver_runtime_entry.py))
- 응답: `Accept: application/json` → `ok`, `solver_run_id`, `optimization_replay`, `solver_summary`, `validation_passed`, 실패 시 `error_code`

Lab JS `Run Solver` → POST run-solver + optimization replay HUD는 **PR9**에서 연동.

## 입력

```text
project_id / slug
latest SolverRun or Reconstruction artifact id
optional solver config
```

## 출력

```text
solver_run_id
optimization_replay payload
final layout preview / materialized map payload
solver_summary
validation_result
```

## Runtime Phase Overview

```text
Phase A — Load Reconstruction Map
Phase B — Build OptimizationInput
Phase C — Capacity Planner / RouteGoal Planner
Phase D — Load GeneTemplate Library
Phase E — Project Genes to Candidate Attempts
Phase F — Geometry Validation
Phase G — Route Probe
Phase H — Candidate Pool Build / Dedupe / Truncate
Phase I — Candidate Selection v0
Phase J — Incremental Commit
Phase K — Route Network Materialization
Phase L — Final Validation
Phase M — Persist / Replay / UI Payload
```

## 금지

- 진입점에서 layout commit·belt/pipe 선설치.
- replay artifact를 solver 입력으로 주입.

## 완료 조건

- [x] 단일 orchestration 함수(또는 서비스)가 A→M 순서를 문서와 동일하게 호출 (`solver_runtime_pipeline` + `solver_runtime_entry`).
- [x] PR7 통합 테스트: persist·replay event·validation read-only.
- [x] HTTP POST 진입·`asteroid_lab_page_context` optimization 트랙 읽기 (PR8).
- [x] Lab JS Run Solver → POST fetch + 12H HUD (PR9).

## 필수 테스트

PR7 — [`implementation_sequence.md`](implementation_sequence.md) § PR7 참조.

## 관련 코드·문서

- [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md) — 첫 단계
- [`phase_m_persist_replay_ui.md`](phase_m_persist_replay_ui.md) — 마지막 단계
- [`asteroid_lab_12_runtime_replay_wiring.md`](../asteroid_lab_12_runtime_replay_wiring.md)

## 다음 Phase

→ [`phase_a_load_reconstruction.md`](phase_a_load_reconstruction.md)
