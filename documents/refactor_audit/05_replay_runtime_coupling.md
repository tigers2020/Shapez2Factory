# Replay / Runtime Coupling Audit

## 결론

- **긍정 판정**: 현재 코드에서 NDJSON/replay 파일을 solver runtime input으로 읽는 직접 경로는 찾지 못했다.
- **부정 판정**: replay/output emission이 placement/recovery/diagnostics 내부에 직접 섞여 있다.
- 즉, **runtime contamination은 아직 낮지만 layering contamination은 높다.**

## 확인한 사실

| 관측 | 파일 | 판정 |
|---|---|---|
| replay reader는 `NotImplementedError` | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/replay/snapshots.py` | runtime input contamination 없음 |
| copy-preview builder가 “replay/trace files are output-side evidence only”를 명시 | `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/solver.py` | 설계 의도는 올바름 |
| import boundary 테스트가 placement/routing/validation의 replay import를 차단 | `tests/unit/shapez_asteroid_v2/test_import_boundaries.py` | 직접 replay import는 잘 막힘 |

## 문제 지점

| File | 문제 | Root cause | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py` | `replay_events` list를 core placement API 인자로 받음 | 알고리즘과 presentation event 생산이 같은 함수에 결합 | `14_step10_replay_ui.md §16.1~§16.3` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass1_outer.py` | `_replay_append`가 event dict schema를 직접 구성 | runtime action과 replay DTO가 분리되지 않음 | `14_step10_replay_ui.md §16.3` | P1 | 높음 | `isolate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/corridor_opening.py` | recovery 실행 중 `TraceEvent` 생성 | recovery domain result와 output trace result 혼합 | `11_step8_recovery.md`, `14_step10_replay_ui.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/diagnostics.py` | diagnostics가 preview frame builder를 호출 | read-only 진단이 UI adapter를 의존 | `05_step1_reconstruction.md`, `14_step10_replay_ui.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/behavior_artifact_collector.py` | behavior artifact가 pass1 replay event 얕은 복사에 의존 | output format이 pass1 internal event shape에 고정 | `14_step10_replay_ui.md` | P2 | 중간 | `isolate` |
| `django_apps/shapez_asteroid/services/v2_behavior_artifact_dump.py` | development-only artifact writer가 view path에 직접 연결 | adapter 위치는 맞지만 application path와 강하게 결합 | `14_step10_replay_ui.md` | P2 | 중간 | `freeze`, `isolate` |

## 프런트 replay 계약 drift

| File | 관측 | 판정 |
|---|---|---|
| `django_apps/web/templates/web/asteroid_optimizer.html` | `solver_replay`, `solver_timeline`, `ui_frames`, `protected_corridors`, `computation_cycle` 중심 로직이 매우 큼 | backend partial pipeline과 구조 drift |
| `django_apps/shapez_asteroid/views.py` | 실제 응답은 `map_timeline`, `existing_layout_analysis`, `reconstruction`, `partial_pipeline` 중심 | UI가 future contract를 앞당겨 가정 |

## 권장 재배치

1. core step 함수는 event sink protocol만 받게 변경
2. `runtime/trace_events.py`는 immutable trace DTO만 유지
3. replay dict 생성은 `runtime/emitters/` 또는 `serialization/replay_adapters.py`로 이동
4. diagnostics는 preview frame count를 직접 계산하지 말고 read-only metrics만 반환
