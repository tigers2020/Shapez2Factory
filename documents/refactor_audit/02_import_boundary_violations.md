# Import Boundary Violations

## 기준

- canonical refs: `02_pipeline_control_flow.md`, `03_data_schema_dto.md`, `14_step10_replay_ui.md`
- structural scan result: `django_apps/asteroid_lab` 내부 다중 파일 SCC 없음
- existing guard: `tests/unit/asteroid_lab/test_service_import_boundaries.py`는 old solver namespace 문자열 포함만 금지

## 주요 위반

| File | Boundary violation | Root cause | Canonical refs | Severity | Confidence | Action |
|---|---|---|---|---|---|---|
| `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay 모듈이 `run_reconstruction(...)`를 import | replay를 output adapter가 아니라 transformation host로 사용 | `14_step10_replay_ui.md` §16, `13_step9_validation.md` | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` | decode frame service가 replay helper를 통해 reconstruction 단계에 간접 의존 | decode/replay/reconstruction 경계가 분리되지 않음 | `02_pipeline_control_flow.md`, `14_step10_replay_ui.md` | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection service가 replay helper + replay recorder + snapshot reload + reconstruction frame까지 소유 | read-only inspection과 replay emission이 한 서비스에 섞임 | `03_data_schema_dto.md` §E, `14_step10_replay_ui.md` | `P1` | High | `split` |
| `django_apps/web/services/asteroid_lab_page_context.py` | web adapter가 replay payload fallback 규칙을 사실상 정본으로 정의 | serializer seam이 solver trace schema보다 UI convenience에 맞춰짐 | `14_step10_replay_ui.md` §16.3 | `P1` | High | `isolate` |
| `django_apps/web/views/public_pages.py` | web view가 replay rebuild 정책까지 직접 판단 | application-service 경계가 얇지 않음 | `02_pipeline_control_flow.md` | `P1` | High | `split` |

## 위반은 아니지만 중요한 관찰

| Observation | Evidence | 의미 |
|---|---|---|
| old solver namespace runtime import는 보이지 않음 | `tests/unit/asteroid_lab/test_service_import_boundaries.py` | v1/v2 import leakage는 현재 문자열 수준에서는 없음 |
| 그러나 canonical/live namespace mismatch는 큼 | live tree는 `asteroid_lab`, canonical docs는 `shapez_asteroid` / `asteroid_mining_layout_v2` | boundary test가 가장 큰 드리프트를 막지 못함 |

## 권장 조치

1. `replay/snapshot_map_replay.py`를 `output_projection` 계층으로 강등하고 reconstruction 계산 호출을 제거한다.
2. `cell_snapshot_service.py`와 `existing_layout_service.py`는 pure DTO 입력만 받는 emitter로 축소한다.
3. web 쪽은 `trace payload serializer` 하나만 호출하고 fallback/merge 규칙은 core serializer로 내린다.
4. import boundary test를 문자열 금지에서 AST graph + allowed-edge 목록 검증으로 올린다.
