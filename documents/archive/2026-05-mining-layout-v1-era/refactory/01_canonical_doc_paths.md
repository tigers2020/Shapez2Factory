# 목표: 정본 문서 경로 혼동 제거

## 배경

- 작업·감사 브리프에 `documents/ai/01_project_overview.md` 등 경로가 쓰이면 저장소에서 파일을 찾지 못하는 경우가 있다.
- **1차 권위(원문)** 는 `documents/Algorithm/mining_solver_cursor_sessions/` 아래 `01`…`14` 분할 파일이다.

## 현재 상태 (Stage 0 정합, 2026-05-12)

- 아래 **14개 파일이 레포지토리에 존재**한다. IDE·검색 도구가 경로를 못 보이는 경우에도, 셸에서 `documents/Algorithm/mining_solver_cursor_sessions/` 를 기준으로 한다.

| 단계 | 파일 (클릭 경로) |
|------|------------------|
| 01 | [`../Algorithm/mining_solver_cursor_sessions/01_project_overview.md`](../Algorithm/mining_solver_cursor_sessions/01_project_overview.md) |
| 02 | [`../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md`](../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md) |
| 03 | [`../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) |
| 04 | [`../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md`](../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md) |
| 05 | [`../Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md`](../Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md) |
| 06 | [`../Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md`](../Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md) |
| 07 | [`../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md`](../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md) |
| 08 | [`../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md`](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) |
| 09 | [`../Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md`](../Algorithm/mining_solver_cursor_sessions/09_step5_pass3_transport.md) |
| 10 | [`../Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md`](../Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md) |
| 11 | [`../Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md`](../Algorithm/mining_solver_cursor_sessions/11_step8_recovery.md) |
| 12 | [`../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md`](../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md) |
| 13 | [`../Algorithm/mining_solver_cursor_sessions/13_step9_validation.md`](../Algorithm/mining_solver_cursor_sessions/13_step9_validation.md) |
| 14 | [`../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md`](../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md) |

- 디렉터리 인덱스(한 페이지 요약): [`../Algorithm/mining_solver_cursor_sessions/README.md`](../Algorithm/mining_solver_cursor_sessions/README.md)
- `documents/ai/`에는 `README.md`, `checklist.md` 등이 있으나 **위 번호 체계의 원문은 `Algorithm/mining_solver_cursor_sessions/`만** 정본으로 본다.

## 목표 상태

- AI·인간 모두가 동일한 **한 줄 canonical base path**를 인용한다:  
  `documents/Algorithm/mining_solver_cursor_sessions/`
- 선택: (A) `documents/ai/`에 정본으로의 인덱스·링크만 두거나, (B) symlink/복사는 하지 않고 `documents/README.md`에 표로 고정한다. **현재 (B) + 본 파일 표가 단일 인덱스다.**

## 작업 항목

1. ~~`documents/README.md` 또는 `documents/ai/README.md`에 **정본 경로 표** 추가~~ → 본 문서 §「현재 상태」표 + [`mining_solver_cursor_sessions/README.md`](../Algorithm/mining_solver_cursor_sessions/README.md) 로 충분할 때는 중복 최소화.
2. AGENTS / 매뉴얼에서 “mining solver 세션 정본” 검색 시 **본 문서 또는 위 README**를 가리키도록 한 줄 보강(중복 서술 최소화).
3. (선택) 레거시 URL/문서에 `documents/ai/08_...` 형태가 남아 있으면 리다이렉트 문구만 추가.

## 검증

- 신규 기여자가 `01_project_overview`만 검색해도 1회 클릭으로 정본에 도달하는지.
- 셸: `Test-Path documents/Algorithm/mining_solver_cursor_sessions` 및 01–14 파일 존재.

## 위험

- 경로 이중 유지 시 한쪽만 갱신되는 드리프트 → **단일 인덱스만 정본**으로 둔다.

## 참고 정본

- `documents/Algorithm/mining_solver_cursor_sessions/*.md` (위 표).
