# Mining solver — Cursor 세션 정본 (1차 권위)

이 디렉터리는 **asteroid mining layout 솔버**의 알고리즘·파이프라인·검증·리플레이를 단계별로 쪼개 둔 **원문 정본**이다. 구현·삭제·drift 감사의 1차 인용은 여기를 따른다.

| 파일 | 주제 |
|------|------|
| [`01_project_overview.md`](01_project_overview.md) | §0–§3 개요·전제 |
| [`02_pipeline_control_flow.md`](02_pipeline_control_flow.md) | 파이프라인·§4 제어 |
| [`03_data_schema_dto.md`](03_data_schema_dto.md) | DTO·스키마 |
| [`04_step0_decode.md`](04_step0_decode.md) | STEP 0 decode |
| [`05_step1_reconstruction.md`](05_step1_reconstruction.md) | STEP 1 reconstruction |
| [`06_step2_pass1_placement.md`](06_step2_pass1_placement.md) | Pass1 |
| [`07_step3_pass2_placement.md`](07_step3_pass2_placement.md) | Pass2 |
| [`08_step4_routing.md`](08_step4_routing.md) | STEP4 routing·placement FSM |
| [`09_step5_pass3_transport.md`](09_step5_pass3_transport.md) | Pass3 |
| [`10_step6_reclaim_loop.md`](10_step6_reclaim_loop.md) | Reclaim |
| [`11_step8_recovery.md`](11_step8_recovery.md) | Recovery §13 |
| [`12_protected_corridor.md`](12_protected_corridor.md) | Protected corridor §14 |
| [`13_step9_validation.md`](13_step9_validation.md) | Final validation §15 |
| [`14_step10_replay_ui.md`](14_step10_replay_ui.md) | Replay·UI §16 |
| [`14_step4_routing_dto_refactor_inventory.md`](14_step4_routing_dto_refactor_inventory.md) | STEP4 DTO·파라미터 인벤토리 |
| [`15_step4_telemetry_field_semantics.md`](15_step4_telemetry_field_semantics.md) | STEP4 텔레메트리 필드 의미 |

- 상위 분할 출처: [`../Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)
- 경로 혼동 방지·인덱스 유지보수: [`../../refactory/01_canonical_doc_paths.md`](../../refactory/01_canonical_doc_paths.md)
- 삭제 감사(초안 → 절단위 인용은 Stage 1): [`../../refactory/algorithm_deviation_deletion_audit.md`](../../refactory/algorithm_deviation_deletion_audit.md)
