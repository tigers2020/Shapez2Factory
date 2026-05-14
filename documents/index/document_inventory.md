# 문서 Inventory

기준일: 2026-05-14  
범위: `documents/`의 주요 설계·플랜·조사·보고 문서. 전체 파일 목록이 아니라 AI context 오염 위험이 큰 문서군의 상태표다.

상태 enum은 [`document_lifecycle.md`](document_lifecycle.md)를 따른다.

## 정본 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`AGENTS.md`](../../AGENTS.md) | `CANON` | workflow spec | YES | 프로젝트 상시 규칙·라우팅 |
| [`.cursor/rules/root.mdc`](../../.cursor/rules/root.mdc) | `CANON` | rule | YES | Cursor 상시 규칙 |
| [`documents/ai/START_HERE.md`](../ai/START_HERE.md) | `CANON` | context entrypoint | YES | AI context 선택 시작점 |
| [`documents/ai/manuals/`](../ai/manuals/) | `CANON` | workflow manuals | YES | 작업 유형별 온디맨드 매뉴얼 |
| [`documents/adr/`](../adr/) | `CANON` | architecture decisions | YES | 정본 spec의 결정 이유 |
| [`documents/game_rules/`](../game_rules/) | `CANON` | domain spec | YES | shapez 2 규칙·도메인 모델 |
| [`documents/research/research_blueprint_grid_coordinates_2026-05-10.md`](../research/research_blueprint_grid_coordinates_2026-05-10.md) | `CANON` | domain invariant | YES | 블루프린트 `x == 0` 불가 정본 |

## 채굴 레이아웃 솔버 정본 후보

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md`](../Algorithm/mining_solver_cursor_sessions/01_project_overview.md) | `CANON` | solver spec | YES | 프로젝트 개요 |
| [`documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md`](../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md) | `CANON` | solver spec | YES | pipeline/recovery 제어 흐름 |
| [`documents/Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) | `CANON` | solver spec | YES | DTO·schema 계약 |
| [`documents/Algorithm/mining_solver_cursor_sessions/04_step0_decode.md`](../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md) | `CANON` | solver spec | YES | STEP0 decode |
| [`documents/Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md`](../Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md) | `CANON` | solver spec | YES | STEP1 reconstruction |
| [`documents/Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md`](../Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md) | `CANON` | solver spec | YES | Pass1 placement |
| [`documents/Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md`](../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md) | `CANON` | solver spec | YES | Pass2 placement |
| [`documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md`](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) | `CANON` | solver spec | YES | STEP4 routing |
| [`documents/Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md`](../Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md) | `CANON` | solver spec | YES | Pass3 transport |
| [`documents/Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md`](../Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md) | `CANON` | solver spec | YES | reclaim loop |
| [`documents/Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md`](../Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md) | `CANON` | solver spec | YES | recovery |
| [`documents/Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md`](../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md) | `CANON` | solver spec | YES | protected corridor |
| [`documents/Algorithm/mining_solver_cursor_sessions/13_step9_validation.md`](../Algorithm/mining_solver_cursor_sessions/13_step9_validation.md) | `CANON` | solver spec | YES | final validation |
| [`documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md`](../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md) | `CANON` | solver spec | YES | replay UI |
| [`documents/archive/2026-05-mining-layout-v1-era/ai/step10_replay_timeline_contract_2026-05-12.md`](../archive/2026-05-mining-layout-v1-era/ai/step10_replay_timeline_contract_2026-05-12.md) | `ARCHIVED` | replay contract snapshot | NO | v1 코드 링크; 정본은 `14_step10_replay_ui.md` |

## 활성 작업·백로그

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | 현재 작업 슬롯 |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | 진행 상태·품질 게이트 |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | v2 MVP 실행 계획 등 잔여; v1 시대 플랜은 아래 아카이브 |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | v1 시대 일부 플랜은 아카이브로 이관됨 |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | 본문 → [`archive/.../refactory/`](../archive/2026-05-mining-layout-v1-era/refactory/) |

## 연구·보고·보관

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | 확정 전 근거. 단, 개별 문서가 정본으로 승격될 수 있음 |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | 로그·회귀 분석 |
| [`documents/archive/2026-05-mining-layout-v1-era/algorithm-root/progress_status_2026-05-10.md`](../archive/2026-05-mining-layout-v1-era/algorithm-root/progress_status_2026-05-10.md) | `REPORT` | progress report | NO | v1 시대 진행 상태 기록 |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | 장기 정본 아님 |
| [`documents/archive/`](../archive/) | `ARCHIVED` | archive | NO | 현재 설계 판단에 쓰지 않음 |
| [`documents/archive/2026-05-mining-layout-v1-era/README.md`](../archive/2026-05-mining-layout-v1-era/README.md) | `ARCHIVED` | archive index | NO | v1 패키지 시대 문서 묶음 인덱스 |
| [`documents/ai/plans/mining_solver_v2_mvp_execution_2026-05-13.md`](../ai/plans/mining_solver_v2_mvp_execution_2026-05-13.md) | `ACTIVE` | execution plan | NO | v2 MVP PR 순서·QUARANTINE 정책 |

## 다음 정리 큐

| 항목 | 상태 | 조치 |
|------|------|------|
| `documents/Algorithm/` 루트 단발 문서 | `ARCHIVED` | [`algorithm-root/`](../archive/2026-05-mining-layout-v1-era/algorithm-root/)로 이관 완료(2026-05-14) |
| `documents/plans/plan_step4_*.md` 계열 | `ARCHIVED` 일부 | v1 경로 참조본은 [`archive/.../plans/`](../archive/2026-05-mining-layout-v1-era/plans/) |
| `documents/refactory/` 본문 | `ARCHIVED` | [`archive/.../refactory/`](../archive/2026-05-mining-layout-v1-era/refactory/); 원위치는 README 리다이렉트만 |
| `documents/canon/` 물리 분리 | 미진행 | 경로 변경 영향이 커서 별도 플랜·승인 후 진행 |
| `documents/reports/YYYY-MM/` 분리 | 부분 완료 | v1 mining 관련 REPORT는 [`archive/.../reports/`](../archive/2026-05-mining-layout-v1-era/reports/) |

## STEP4 telemetry / DTO index additions

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md`](../Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md) | `CANON` | solver spec | YES | STEP4 DTO boundary inventory |
| [`documents/Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md`](../Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md) | `CANON` | telemetry spec | YES | STEP4 route-failure telemetry field semantics |
