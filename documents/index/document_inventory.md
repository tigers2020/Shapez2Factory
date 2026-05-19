# 문서 Inventory

기준일: 2026-05-15  
범위: `documents/`의 주요 설계·계획·조사·보고·보관 문서. 전체 파일 목록이 아니라 AI context 선택을 위한 authority 지도다.

상태 enum은 [`document_lifecycle.md`](document_lifecycle.md)를 따른다.

## 정본 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | 라우팅·문서 권위·승인 금지 |
| [`.cursor/rules/shapez2-core.mdc`](../../.cursor/rules/shapez2-core.mdc) | `CANON` | rule | YES | Cursor 단일 alwaysApply (Caveman·게이트·검증) |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context 선택 시작점 |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | 작업 유형별 온디맨드 매뉴얼 |
| [`documents/index/document_lifecycle.md`](document_lifecycle.md) | `CANON` | document governance | YES | 문서 상태 enum과 읽기 우선순위 |
| [`documents/index/document_inventory.md`](document_inventory.md) | `CANON` | document governance | YES | 현재 문서 authority 지도 |
| [`documents/adr/`](../adr/) | `CANON` | architecture decisions | YES | 정본 spec의 결정 이유 |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 규칙과 solver domain abstraction |
| [`documents/game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) | `CANON` | domain throughput | YES | Asteroid Miner/Pump·Space Belt/Pipe 절대 L/min·shapes/min |
| [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../research/research_blueprint_grid_coordinates_2026-05-10.md) | `CANON` | domain invariant | YES | blueprint grid coordinate invariant |

## Active 작업·백로그

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | 현재 작업 흐름 |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | 진행 상태와 검증 게이트 |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | 완료 근거 미확정 계획 |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | 범위 한정 플랜 |
| [`documents/Algorithm/solver_runtime/`](../Algorithm/solver_runtime/) | `ACTIVE` | solver button pipeline | NO | Phase A–M·PR1–7; 충돌 해소 [`ARCHITECTURE_RECONCILIATION.md`](../Algorithm/solver_runtime/ARCHITECTURE_RECONCILIATION.md) |

## Research·Report

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | 조사·근거. 개별 문서만 정본 승격 가능 |
| [`documents/research/research_shapez2_space_transport_throughput_2026-05-18.md`](../research/research_shapez2_space_transport_throughput_2026-05-18.md) | `SUPERSEDED` | game throughput | NO | → [`game_rules/shapez2_asteroid_space_transport_throughput.md`](../game_rules/shapez2_asteroid_space_transport_throughput.md) |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | report 묶음 라우팅. 정본 계약 아님 |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | 로그/복사본 분석 |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | 장기 메모. 정본 아님 |
| [`documents/Algorithm/README.md`](../Algorithm/README.md) | `RESEARCH` | algorithm memos index | NO | Asteroid Lab optimization 시리즈·초안(`drafts/`). 진입점 README. 구현 정본은 코드·CANON 우선 |

## Archive·완료 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | archive bucket 지도 |
| [`documents/archive/2026-05-completed/README.md`](../archive/2026-05-completed/README.md) | `COMPLETED` | completed index | NO | 2026-05 완료 묶음 |
| [`documents/archive/completed-implementation/README.md`](../archive/completed-implementation/README.md) | `COMPLETED` | completed plan/research pairs | NO | 구현 완료 stem별 pair |
| [`documents/archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](../archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | obsolete plan set | NO | Django-first 전환 전 계획 |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | v1-era 트리 제거됨. 과거 본문은 git 기록 참고 |

## 다음 정리 후보

| 항목 | 현재 상태 | 조치 |
|------|----------|------|
| 루트 `v2_behavior_artifact_*.json` | generated artifact | 실행 산출물 정리 대상으로 별도 판단 |

## 2026-05-15 구조 반영

- `django_apps.shapez_asteroid` 및 `tests/unit/shapez_asteroid*`는 제거되었다.
- 채굴 레이아웃 솔버 canonical step 스펙(`documents/Algorithm/mining_solver_cursor_sessions/`) 및 관련 archive/plan 대량 정리는 **git 기록**으로만 남는다.
