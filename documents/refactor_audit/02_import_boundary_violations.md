# Import Boundary Violations

## 요약

- 구조 테스트는 `v2 -> v1` 직접 import를 잘 막고 있다.
- 그러나 `v2` 내부에서는 **domain/runtime/placement 사이의 패키지 경계**와 **routing/placement 경계**가 깨져 있다.
- 정적 SCC 결과:
  - `domain`
  - `domain.dto`
  - `placement.placement_fsm`
  - `runtime`
  - `runtime.trace_events`

## 위반 목록

| File | 위반 유형 | 증거 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/__init__.py` | domain이 placement/runtime를 재export | `placement.placement_fsm`, `TraceEvent`를 domain public surface로 노출 | `03_data_schema_dto.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/dto.py` | DTO alias가 runtime에 의존 | `runtime.trace_events` import 후 `TraceEvent` re-export | `03_data_schema_dto.md`, `14_step10_replay_ui.md` | P1 | 높음 | `isolate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/runtime/trace_events.py` | runtime이 domain package helper에 의존 | `domain.trace_semantics` import | `14_step10_replay_ui.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/runtime/__init__.py` | runtime package가 Phase 7 split TODO를 안고 DTO cycle에 남아 있음 | docstring이 mixed concern을 직접 언급 | `03_data_schema_dto.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/corridor_probe.py` | routing이 placement internals에 의존 | `placement.bundle_candidate`, `placement.pass1_outer`, `placement.pass2_route_probe` import | `08_step4_routing.md` | P1 | 높음 | `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/step4_corridor_recovery.py` | routing facade가 placement recovery를 단순 재노출 | `placement.corridor_opening.step4_corridor_opening_recovery` import | `08_step4_routing.md`, `11_step8_recovery.md` | P1 | 높음 | `deprecate`, `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/reconstruction/diagnostics.py` | diagnostics가 preview/UI adapter를 지연 import | `_preview_timeline_fields`에서 `preview_reconstruction_timeline` 호출 | `14_step10_replay_ui.md` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/corridor.py` | domain corridor DTO가 runtime TraceEvent를 품음 | `trace_rows: tuple[TraceEvent, ...]` | `03_data_schema_dto.md`, `14_step10_replay_ui.md` | P1 | 높음 | `isolate` |

## 직접 위반은 없지만 감시가 필요한 경계

| File/Area | 관측 | 해석 | 조치 |
|---|---|---|---|
| `tests/unit/shapez_asteroid_v2/test_import_boundaries.py` | `v2 -> v1`, `validation -> replay`, Django import 차단은 잘 잡음 | 바깥 경계는 양호 | 유지 |
| `tests/unit/shapez_asteroid_v2/test_domain_import_boundaries.py` | domain이 preview/replay/runtime import를 막도록 설계됨 | 그러나 `domain.__init__`와 `domain.dto` 자체는 별도 허용 구멍 | 테스트 확장 |
| `validation/final_validation.py` | route creator import는 없음, `routing.connectivity`만 사용 | “validation이 route 생성” 위반은 현재 없음 | freeze 후 assertion 강화 |

## 권장 경계 재정의

1. `domain/`
   - 순수 dataclass/enum/coordinate/semantic validator만 유지
   - `__init__.py`에서 placement/runtime 재export 제거

2. `runtime/`
   - `TraceEvent`와 serializer-friendly trace adapter만 유지
   - domain package root가 아니라 leaf module에만 의존

3. `routing/`
   - `placement` helper import 제거
   - corridor probe / trunk goal / exterior predicate 공통 유틸을 `routing/shared.py` 또는 `domain/routing_support.py`로 승격

4. `reconstruction/diagnostics.py`
   - preview frame count 진단을 별도 UI adapter로 이동
