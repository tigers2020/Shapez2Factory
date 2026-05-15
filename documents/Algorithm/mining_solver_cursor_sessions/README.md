# Mining solver cursor sessions canonical specs

이 디렉터리는 asteroid mining layout v2의 algorithm contract를 단계별로 나눈 canonical spec이다. 구현, 테스트, 보고서, 로그가 이 문서와 충돌하면 이 문서가 우선한다.

## Canonical documents

| 파일 | 주제 |
|---|---|
| [`01_project_overview.md`](01_project_overview.md) | 프로젝트 개요, 전제, 전역 불변식 |
| [`02_pipeline_control_flow.md`](02_pipeline_control_flow.md) | pipeline control flow |
| [`03_data_schema_dto.md`](03_data_schema_dto.md) | DTO/schema, semantic fields |
| [`04_step0_decode.md`](04_step0_decode.md) | STEP 0 decode, STEP 0.5 ExistingLayoutAnalysis |
| [`05_step1_reconstruction.md`](05_step1_reconstruction.md) | STEP 1 reconstruction |
| [`06_step2_pass1_placement.md`](06_step2_pass1_placement.md) | STEP 2 Pass1 placement |
| [`07_step3_pass2_placement.md`](07_step3_pass2_placement.md) | STEP 3 Pass2 placement |
| [`08_step4_routing.md`](08_step4_routing.md) | STEP 4 routing, PlacementCommitState FSM |
| [`09_step5_pass3_transport.md`](09_step5_pass3_transport.md) | STEP 5 Pass3 transport reconstruction |
| [`10_step6_reclaim_loop.md`](10_step6_reclaim_loop.md) | STEP 6 Reclaim, optional post-reclaim Pass3 rerun |
| [`11_step8_recovery.md`](11_step8_recovery.md) | STEP 8 bounded recovery branch |
| [`12_protected_corridor.md`](12_protected_corridor.md) | protected corridor lifecycle |
| [`13_step9_validation.md`](13_step9_validation.md) | STEP 9 final validation |
| [`14_step10_replay_ui.md`](14_step10_replay_ui.md) | STEP 10 replay/UI output contracts |

## Supplemental / needs-review documents

아래 문서는 같은 디렉터리에 있지만 이번 감사 기준으로 사용자 지정 canonical 01-14 범위 밖이다. 구현 판단에서 01-14와 충돌하면 01-14가 우선한다.

| 파일 | 상태 | 메모 |
|---|---|---|
| [`14_step4_routing_dto_refactor_inventory.md`](14_step4_routing_dto_refactor_inventory.md) | needs_review | `14_step10_replay_ui.md`와 번호가 충돌한다. STEP4 DTO 보조 인벤토리로 분리 검토. |
| [`15_step4_telemetry_field_semantics.md`](15_step4_telemetry_field_semantics.md) | needs_review | telemetry/output semantics 보조 문서로 유지할지 정본 승격할지 검토 필요. |

## Global rules

- Logs, NDJSON, replay_events, behavior artifacts, solver_summary는 output evidence only다. algorithm input으로 사용하지 않는다.
- ExistingLayoutAnalysis는 read-only context다.
- Reconstruction만 `mineable_placement_cells`를 생성한다.
- Pass1/Pass2는 provisional placement만 만든다.
- cheap escape path는 final route가 아니다.
- STEP4가 fixed output stub 기반 routing과 route confirmation을 소유한다.
- Final validation은 assertion-only다.
- Recovery는 bounded branch이며 항상 실행되는 linear phase가 아니다.
- Historical reports and prompts do not override these specs.

## Source and archive notes

- v1-era long-form/root documents are historical only under [`../../archive/2026-05-mining-layout-v1-era/`](../../archive/2026-05-mining-layout-v1-era/README.md).
- 2026-05-15 audit results: [`../../reports/documentation_audit/README.md`](../../reports/documentation_audit/README.md).
