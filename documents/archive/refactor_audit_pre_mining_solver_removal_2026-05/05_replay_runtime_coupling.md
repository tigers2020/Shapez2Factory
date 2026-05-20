# Replay / Runtime Coupling

## canonical baseline

- `14_step10_replay_ui.md` §16: replay는 trace/output/UI 계층
- `13_step9_validation.md`: validation은 assertion gate
- `03_data_schema_dto.md` §E: existing layout analysis는 read-only context

## 현재 coupling evidence

| File | Coupling evidence | Root cause | Risk severity | Confidence | Action |
|---|---|---|---|---|---|
| `django_apps/asteroid_lab/replay/snapshot_map_replay.py` | replay 모듈이 `run_reconstruction(...)` 호출 | replay utility에 algorithm projection을 몰아넣음 | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/cell_snapshot_service.py` | decode frame 기록이 `build_cleanup_and_reconstruction_rows(...)`에 의존 | decode frame emission과 replay projection이 결합 | `P1` | High | `split` |
| `django_apps/asteroid_lab/services/existing_layout_service.py` | inspection replay 기록이 snapshot 재구성 + reconstruction overlay + issue filtering까지 수행 | inspection read-model과 replay emitter 혼합 | `P1` | High | `split` |
| `django_apps/web/services/asteroid_lab_page_context.py` | serializer가 fallback/full_map/diff/summary를 조합해 UI contract를 재작성 | canonical trace serializer 부재 | `P1` | High | `isolate` |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | UI가 `full_map`, `cell_overlay_json`, `diff`, issue overlays를 독자 해석 | rendering concern이 payload semantics를 흡수 | `P1` | High | `split` |

## 핵심 문제

현재 replay는 "runtime output"이 아니라 "runtime 계산을 불러와 화면용 shape로 가공하는 중간 계층"이다. 이 구조에서는:

- replay 변경이 reconstruction 동작과 동시에 얽힌다
- backend contract가 흔들려도 UI fallback이 drift를 가린다
- canonical `trace_event` / `computation_cycle` / streaming 규칙으로 이동하기 어렵다

## early-phase 금지 사항

아래는 replay coupling 분리 전에는 건드리지 말아야 한다.

- `django_apps/asteroid_lab/reconstruction/pipeline.py`
- `django_apps/asteroid_lab/reconstruction/fill.py`
- `tests/unit/asteroid_lab/test_reconstruction_topology.py`

## 권장 분리 방향

1. pure runtime
   - `reconstruction/*`
   - `snapshots/existing_layout_inspection.py`
2. projection adapter
   - snapshot DTO → replay frame rows
3. persistence adapter
   - replay row append / snapshot row save
4. UI serializer
   - persisted row → canonical API payload

## 관련 테스트 공백

- replay module이 runtime import를 하지 않는지 확인하는 test 없음
- `trace_event` schema alignment test 없음
- `computation_cycle` / streaming cadence test 없음
