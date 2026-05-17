# 문서 Inventory

기준일: 2026-05-16  
범위: `documents/`의 주요 설계·계획·조사·보고·보관 문서. 전체 파일 목록이 아니라 AI context 선택을 위한 authority 지도다.

상태 enum은 [`document_lifecycle.md`](document_lifecycle.md)를 따른다.

## 정본 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | 프로젝트 상시 규칙과 routing |
| [`.cursor/rules/root.mdc`](../../.cursor/rules/root.mdc) | `CANON` | rule | YES | Cursor 상시 규칙 |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context 선택 시작점 |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | 작업 유형별 온디맨드 매뉴얼 |
| [`documents/index/document_lifecycle.md`](document_lifecycle.md) | `CANON` | document governance | YES | 문서 상태 enum과 읽기 우선순위 |
| [`documents/index/document_inventory.md`](document_inventory.md) | `CANON` | document governance | YES | 현재 문서 authority 지도 |
| [`documents/adr/`](../adr/) | `CANON` | architecture decisions | YES | 정본 spec의 결정 이유 |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 규칙과 solver domain abstraction |
| [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../research/research_blueprint_grid_coordinates_2026-05-10.md) | `CANON` | domain invariant | YES | blueprint grid coordinate invariant |

## Active 작업·백로그

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | 현재 작업 흐름 |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | 진행 상태와 검증 게이트 |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | 완료 근거 미확정 계획 |
| [`documents/ai/plans/`](../ai/plans/README.md) | `ACTIVE` | scoped plans | NO | 범위 한정 플랜 슬롯; 채굴 고아 플랜은 archive로 이동됨(README 참고) |
| [`documents/plans/plan_solver_graph_horizontal_layout_2026-05-01.md`](../plans/plan_solver_graph_horizontal_layout_2026-05-01.md) | `ACTIVE` | plan | NO | `solver_graph_layout.js`에 수평 배치 로직 대부분 반영됨; 완료 확정 시 archive 검토 |

## Research·Report

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | 조사·근거. 개별 문서만 정본 승격 가능 |
| [`documents/research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md`](../research/research_asteroid_server_coords_layout_fingerprint_2026-05-16.md) | `RESEARCH` | asteroid lab memo | NO | server 좌표·layout fingerprint. CANON 아님 |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | report 묶음 라우팅. 정본 계약 아님 |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | 로그/복사본 분석 슬롯. **현재 체크아웃에 파일 없음**; 과거 보고는 git 기록 |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | 장기 메모. 정본 아님 |

## Archive·완료 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | archive bucket 지도 |
| [`documents/archive/2026-05-completed/README.md`](../archive/2026-05-completed/README.md) | `COMPLETED` | completed index | NO | 2026-05 완료 묶음 |
| [`documents/archive/completed-implementation/README.md`](../archive/completed-implementation/README.md) | `COMPLETED` | completed plan/research pairs | NO | 구현 완료 stem별 pair |
| [`documents/archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](../archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | obsolete plan set | NO | Django-first 전환 전 계획 |
| [`documents/archive/2026-05-orphan-mining-layout-plans-after-app-removal/`](../archive/2026-05-orphan-mining-layout-plans-after-app-removal/README.md) | `ARCHIVED` | orphan mining plans | NO | 솔버 제거 후 전제 코드 없는 placement 플랜 3건 |
| [`documents/archive/refactor_audit_pre_mining_solver_removal_2026-05/`](../archive/refactor_audit_pre_mining_solver_removal_2026-05/README.md) | `ARCHIVED` | audit bundle | NO | 제거된 mining_solver_cursor_sessions 인용 감사. 역사 전용 |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | v1-era 트리 제거됨. 실질 본문은 `research/`로 이전 |

## 다음 정리 후보

| 항목 | 현재 상태 | 조치 |
|------|----------|------|
| 루트 `v2_behavior_artifact_*.json` | generated artifact | 실행 산출물 정리 대상으로 별도 판단 |

## 2026-05-15 구조 반영

- `django_apps.shapez_asteroid` 및 `tests/unit/shapez_asteroid*`는 제거되었다.
- 채굴 레이아웃 솔버 canonical step 스펙(`documents/Algorithm/mining_solver_cursor_sessions/`) 및 관련 archive/plan 대량 정리는 **git 기록**으로만 남는다.

## 2026-05-16 문서 정리

- 고아 채굴 placement 플랜·감사 묶음은 위 archive 표 참고.
- `documents/meta/chat.md` 비프로젝트 덤프는 제거(원문 필요 시 git 기록).
