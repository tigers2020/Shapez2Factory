# Decoded existing layout — 중간 모델·문서 접목 플랜

**상태**: 문서 정본 반영(2026-05-10). 구현은 별도 커밋·게이트.

## 핵심 설계 문장

```text
디코드된 기존 island 레이아웃은 reconstruction 전용 입력이 아니라 solver context다.
```

`mineable_placement_cells`·asteroid shell 복원과 **혼동하면 모델이 오염**된다.

## 문서 정본 위치

| 순서 | 파일 |
| ---: | --- |
| 1 | [`03_data_schema_dto.md`](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) — `ExistingLayoutAnalysis` 등 DTO |
| 2 | [`04_step0_decode.md`](../Algorithm/mining_solver_cursor_sessions/04_step0_decode.md) — STEP 0.5 |
| 3 | [`05_step1_reconstruction.md`](../Algorithm/mining_solver_cursor_sessions/05_step1_reconstruction.md) — 경계 |
| 4 | [`08_step4_routing.md`](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) — trunk seed |
| 5 | [`12_protected_corridor.md`](../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md) — 보호 등급 |
| 6 | [`13_step9_validation.md`](../Algorithm/mining_solver_cursor_sessions/13_step9_validation.md) — existing vs final |
| 7 | [`14_step10_replay_ui.md`](../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md) — 레이어 |
| 8 | [`02_pipeline_control_flow.md`](../Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md) — STEP 0.5 슬롯 |

## 구현 시 범위 (요약)

- **당장**: 분석 모듈·copy-preview API·`compute_transport_components` 등 순수 함수.
- **계약 우선**: `ExistingLayoutSolverHints`는 DTO에 먼저 고정; Pass3 trunk 보호 **정책 구현**은 deferred.
- **DB 영속화**: 후순위(본 플랜 범위 밖).

## 관련

- [`documents/ai/current_plan.md`](../ai/current_plan.md) — P0.5 한 줄.
- Cursor 플랜 초안: `decoded_island_layout_model` (구현 전 리서치·승인 게이트는 프로젝트 규칙 준수).
