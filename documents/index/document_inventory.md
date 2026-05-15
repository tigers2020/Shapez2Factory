# 문서 Inventory

기준일: 2026-05-15
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

## Mining solver canonical specs

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/Algorithm/mining_solver_cursor_sessions/README.md`](../Algorithm/mining_solver_cursor_sessions/README.md) | `CANON` | solver spec index | YES | session spec map |
| [`documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md`](../Algorithm/mining_solver_cursor_sessions/01_project_overview.md) | `CANON` | solver spec | YES | 프로젝트 개요 |
| [`documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md`](../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md) | `CANON` | solver spec | YES | pipeline/recovery control flow |
| [`documents/Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) | `CANON` | solver spec | YES | DTO/schema 계약 |
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
| [`documents/Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md`](../Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md) | `ACTIVE` | supplemental inventory | NO | STEP4 DTO boundary inventory. 번호 충돌 때문에 01-14 canonical step docs보다 낮은 권위. |
| [`documents/Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md`](../Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md) | `ACTIVE` | supplemental telemetry note | NO | STEP4 route-failure telemetry semantics. telemetry 보조 문서로 검토 중. |

## Active 작업·백로그

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/ai/current_plan.md`](../ai/current_plan.md) | `ACTIVE` | work queue | NO | 현재 작업 흐름. 일부 오래된 문구는 archive 링크로만 해석한다. |
| [`documents/ai/checklist.md`](../ai/checklist.md) | `ACTIVE` | checklist | NO | 진행 상태와 검증 게이트 |
| [`documents/Algorithm/checklist.md`](../Algorithm/checklist.md) | `ACTIVE` | solver checklist | NO | v2 sequence 관리 체크리스트 |
| [`documents/ai/plans/mining_solver_v2_mvp_execution_2026-05-13.md`](../ai/plans/mining_solver_v2_mvp_execution_2026-05-13.md) | `ACTIVE` | execution plan | NO | v2 MVP PR 순서와 quarantine 정책 |
| [`documents/ai/ACTIVE_v2_dto_slice_reconstruction.md`](../ai/ACTIVE_v2_dto_slice_reconstruction.md) | `ACTIVE` | execution note | NO | v2 DTO slice/re-export 진행 상태 |
| [`documents/ai/plans/v2_copy_preview_behavior_artifact.md`](../ai/plans/v2_copy_preview_behavior_artifact.md) | `ACTIVE` | plan | NO | v2 copy-preview behavior artifact |
| [`documents/plans/`](../plans/) | `ACTIVE` | plans/backlog | NO | 완료 근거 미확정 계획. archive 이동 전 검증 필요 |
| [`documents/ai/plans/`](../ai/plans/) | `ACTIVE` | scoped plans | NO | v2와 남은 solver planning |

## Research·Report

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/research/`](../research/) | `RESEARCH` | research | NO | 조사·근거. 개별 문서만 정본 승격 가능 |
| [`documents/research/runtime_semantic_verification.md`](../research/runtime_semantic_verification.md) | `RESEARCH` | runtime verification note | NO | v2/solver semantic verification 근거 |
| [`documents/reports/2026-05/path_a_post_diagnostic_audit_2026-05-13.md`](../reports/2026-05/path_a_post_diagnostic_audit_2026-05-13.md) | `REPORT` | audit report | NO | Path A post diagnostic audit |
| [`documents/reports/2026-05/pass12_expected_preserve_loss_acceptance_2026-05-13.md`](../reports/2026-05/pass12_expected_preserve_loss_acceptance_2026-05-13.md) | `REPORT` | acceptance report | NO | Pass12 expected preserve loss acceptance |
| [`documents/reports/README.md`](../reports/README.md) | `REPORT` | report index | NO | report 묶음 라우팅. 정본 계약 아님 |
| [`documents/reports/documentation_audit/README.md`](../reports/documentation_audit/README.md) | `REPORT` | documentation audit index | NO | 2026-05-15 문서/코드 대조 감사 |
| [`documents/debug/`](../debug/) | `REPORT` | debug report | NO | 로그/복사본 분석 |
| [`documents/notes/`](../notes/) | `REPORT` | notes | NO | 장기 메모. 정본 아님 |

## Archive·완료 문서

| 문서 | 상태 | 종류 | 정본 여부 | 비고 |
|------|------|------|-----------|------|
| [`documents/archive/README.md`](../archive/README.md) | `CANON` | archive index | YES | archive bucket 지도 |
| [`documents/archive/2026-05-mining-layout-v1-era/README.md`](../archive/2026-05-mining-layout-v1-era/README.md) | `ARCHIVED` | archive index | NO | v1 package era 문서 묶음 |
| [`documents/archive/2026-05-completed/README.md`](../archive/2026-05-completed/README.md) | `COMPLETED` | completed index | NO | 2026-05 완료 묶음 |
| [`documents/archive/completed-implementation/README.md`](../archive/completed-implementation/README.md) | `COMPLETED` | completed plan/research pairs | NO | 구현 완료 stem별 pair |
| [`documents/archive/obsolete-src-shapez2-solver-plans-2026-05-01/`](../archive/obsolete-src-shapez2-solver-plans-2026-05-01/) | `ARCHIVED` | obsolete plan set | NO | Django-first 전환 전 계획 |
| [`documents/refactory/README.md`](../refactory/README.md) | `ARCHIVED` | redirect | NO | 본문은 v1-era archive/refactory에 있음 |

## 다음 정리 후보

| 항목 | 현재 상태 | 조치 |
|------|----------|------|
| `documents/plans/plan_pass12_*.md` | `ACTIVE` | v2 구현/검증 완료 근거 확인 뒤 `COMPLETED` 또는 v1-era archive 판정 |
| `documents/ai/plans/placement_stub_escape_gate_p2_2026-05-09.md` 등 2026-05-09 계획 | `ACTIVE` | v2와 무관한 v1-era 계획인지 확인 후 archive 후보 |
| `documents/reports/2026-05/` | `REPORT` | 정본 반영이 필요하면 Algorithm spec 또는 ADR로 승격 |
| `documents/Algorithm/mining_solver_cursor_sessions.zip` | generated/reference artifact | 정본 문서 아님. 필요 시 산출물 정리 정책에서 처리 |
| 루트 `v2_behavior_artifact_*.json` | generated artifact | 문서 archive가 아니라 실행 산출물 정리 대상으로 별도 판단 |

## 2026-05-15 최신 구조 반영

- `asteroid_mining_layout_v2`에는 `adapters/`, `decode/`, `routing/corridor_probe.py`, `routing/step4_corridor_recovery.py`, `placement/corridor_opening.py`, `domain/corridor.py`가 포함된다.
- `tests/unit/shapez_asteroid_v2/`에는 corridor probe와 min-cost egress carving 회귀 테스트가 포함된다.
- 위 파일들은 현재 v2 작업 경계로 보며, v1-era archive 문서의 구현 계약을 되살리는 근거로 쓰지 않는다.
