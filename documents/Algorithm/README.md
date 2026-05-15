# Algorithm 문서 인덱스

이 디렉터리는 algorithm 계약과 관련 체크리스트를 둔다. asteroid mining solver의 현재 canonical authority는 [`mining_solver_cursor_sessions/`](mining_solver_cursor_sessions/README.md)다.

## canonical step order

| 단계 | canonical 문서 | 요약 |
|---|---|---|
| STEP 0 decode | [`04_step0_decode.md`](mining_solver_cursor_sessions/04_step0_decode.md) | copy code/decode payload를 solver 입력 DTO로 정규화한다. |
| STEP 0.5 ExistingLayoutAnalysis | [`03_data_schema_dto.md`](mining_solver_cursor_sessions/03_data_schema_dto.md), [`04_step0_decode.md`](mining_solver_cursor_sessions/04_step0_decode.md) | decoded layout의 read-only context. mineable cells를 만들지 않는다. |
| STEP 1 reconstruction | [`05_step1_reconstruction.md`](mining_solver_cursor_sessions/05_step1_reconstruction.md) | shell/interior/equipment footprint로 `mineable_placement_cells`를 만든다. |
| STEP 2 Pass1 | [`06_step2_pass1_placement.md`](mining_solver_cursor_sessions/06_step2_pass1_placement.md) | outer-first provisional placement. cheap escape는 probe-only. |
| STEP 3 Pass2 | [`07_step3_pass2_placement.md`](mining_solver_cursor_sessions/07_step3_pass2_placement.md) | internal provisional placement. route confirmation 없음. |
| STEP 4 routing | [`08_step4_routing.md`](mining_solver_cursor_sessions/08_step4_routing.md) | fixed output stub에서 route를 시작하고 `ROUTED_CONFIRMED`를 소유한다. |
| STEP 5 Pass3 | [`09_step5_pass3_transport.md`](mining_solver_cursor_sessions/09_step5_pass3_transport.md) | mining-priority transport reconstruction. |
| STEP 6 Reclaim | [`10_step6_reclaim_loop.md`](mining_solver_cursor_sessions/10_step6_reclaim_loop.md) | protected corridor와 route replacement 계약 아래 reclaim을 수행한다. |
| STEP 7 optional post-reclaim Pass3 rerun | [`10_step6_reclaim_loop.md`](mining_solver_cursor_sessions/10_step6_reclaim_loop.md), [`09_step5_pass3_transport.md`](mining_solver_cursor_sessions/09_step5_pass3_transport.md) | reclaim 이후 연결성 break가 있으면 제한적으로 Pass3를 재실행한다. |
| STEP 8 Recovery branch | [`11_step8_recovery.md`](mining_solver_cursor_sessions/11_step8_recovery.md) | bounded recovery branch. 항상 linear로 실행되는 단계가 아니다. |
| STEP 9 Final validation | [`13_step9_validation.md`](mining_solver_cursor_sessions/13_step9_validation.md) | assertion-only validation gate. |
| STEP 10 Replay/UI | [`14_step10_replay_ui.md`](mining_solver_cursor_sessions/14_step10_replay_ui.md) | replay/trace/UI output 계약. algorithm input 금지. |

## 보조 문서

- [`checklist.md`](checklist.md): 구현 진척과 검증 체크리스트. 정본 spec이 아니다.
- `mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md`, `15_step4_telemetry_field_semantics.md`: canonical directory 안에 있으나 이번 감사 기준으로는 supplemental/needs-review 문서다. 01-14 canonical step docs와 충돌하면 01-14가 우선한다.

## 감사 자료

- [`../reports/documentation_audit/README.md`](../reports/documentation_audit/README.md): 2026-05-15 문서/코드 대조 감사.
