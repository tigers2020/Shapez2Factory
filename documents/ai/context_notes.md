# 컨텍스트 메모

## Asteroid Lab: 장비 번들 외곽선 (2026-05-16)

- 추출기·확장기 4방 BFS는 `django_apps/asteroid_lab/snapshots/equipment_bundles.py`의 `build_equipment_bundles`; 리플레이 `cell_overlay_json.equipment_bundles` + Lab JS에서 `full_map` 렌더 직후 테두리 패스. 솔버 입력 아님.

## STEP4 `no_route_exhausted` 샘플 (2026-05-12)

- NDJSON에서 `routing_failures` 기준 대표 샘플·질문별 요약: [`documents/debug/step4_no_route_exhausted_sample_report_2026-05-12.md`](../debug/step4_no_route_exhausted_sample_report_2026-05-12.md)
- 추출 스크립트(프로덕션 비포함): `scripts/debug/extract_step4_no_route_exhausted_samples.py`
