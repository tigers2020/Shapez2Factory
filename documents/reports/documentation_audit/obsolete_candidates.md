# 중복·obsolete 후보

> 생성: 2026-05-15. 자동 삭제하지 않는다. 아래 후보는 정본과 비교하거나 archive 정책에 따라 사람이 결정한다.

| path | why obsolete/conflicting | replacement canonical document | recommended action |
|---|---|---|---|
| `documents/refactory/README.md` | v1-era refactory redirect. 현재 v2 정본이 아님. | `documents/Algorithm/mining_solver_cursor_sessions/README.md` | keep_as_history |
| `documents/archive/2026-05-mining-layout-v1-era/**` | old `asteroid_mining_layout/` 경로와 v1 solver assumptions가 많다. | `documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md` through `14_step10_replay_ui.md` | keep_as_history |
| `documents/archive/2026-05-mining-layout-v1-era/algorithm-root/Shapez2 Asteroid Mining Solver logic.md` | 원본/장문 algorithm root로 보이나 현재 정본은 session split 01-14. 중복 출처로만 사용해야 한다. | `documents/Algorithm/mining_solver_cursor_sessions/README.md` | keep_as_history |
| `documents/archive/2026-05-mining-layout-v1-era/plans/plan_step4_no_route_exhausted_recovery_2026-05-12.md` | `latest.ndjson`를 분석 증거로 사용한다. algorithm input으로 오해될 위험. | `11_step8_recovery.md`, `14_step10_replay_ui.md` | keep_as_history |
| `documents/archive/2026-05-mining-layout-v1-era/plans/plan_pass3_internal_transport_optimization_warning_2026-05-13.md` | 로그 관측 기반 경고. Pass3 canonical rule로 승격되지 않음. | `09_step5_pass3_transport.md` | keep_as_history |
| `documents/Algorithm/mining_solver_cursor_sessions/14_step4_routing_dto_refactor_inventory.md` | canonical directory 안에 있으나 사용자 지정 01-14 canonical list 밖이고 번호가 `14`와 충돌한다. | `08_step4_routing.md`, `03_data_schema_dto.md` | human review, possibly rewrite_summary_only |
| `documents/Algorithm/mining_solver_cursor_sessions/15_step4_telemetry_field_semantics.md` | canonical directory 안 보조 telemetry 문서. output evidence와 algorithm input 경계가 오해될 수 있다. | `14_step10_replay_ui.md`, `03_data_schema_dto.md` | human review, possibly merge_into_index |
| `documents/ai/checklist.md` old v1 sections | 현재 checklist 안에 v1 `asteroid_mining_layout` 참조와 v2 current 항목이 혼재한다. | `documents/Algorithm/checklist.md`, `documents/reports/documentation_audit/code_doc_crosscheck.md` | rewrite_summary_only |
| `documents/plans/plan_pass12_*.md`, `documents/plans/plan_pass2_island_fallback_gate_2026-05-13.md` | active/backlog일 수 있으나 v1/pass12 terminology가 현재 v2 skeleton과 섞일 위험. | `06_step2_pass1_placement.md`, `07_step3_pass2_placement.md`, `08_step4_routing.md` | human review |
| root `v2_behavior_artifact_*.json` | generated output이 root에 쌓여 문서/소스와 혼동될 수 있다. | none; generated artifact policy | delete_after_human_review or move outside repo |
| `var/asteroid_mining_layout_debug/**` | debug output evidence. canonical algorithm input 아님. | `14_step10_replay_ui.md` output-only rule | keep_as_generated_output |
| `documents/samples/*.json` | sample/decode output. 정본 spec가 아님. | relevant game_rules or Algorithm docs | keep_as_history |
