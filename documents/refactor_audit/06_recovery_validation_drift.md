# Recovery / Validation Drift

## 총평

- recovery와 validation은 모두 정본 대비 **축소 구현** 상태다.
- validation은 “route 생성은 하지 않는다” 원칙은 지키고 있지만, 너무 관대해서 assertion gate 역할이 약하다.
- recovery는 별도 bounded branch라기보다 placement helper 안의 corrective mutation으로 보인다.

## validation drift

| File | 관측 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | `transport_cells`가 비어 있으면 connectivity를 자동 통과 | `13_step9_validation.md §15.2` | P0 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | external seed가 없으면 connectivity를 자동 통과 | `13_step9_validation.md §15.2` | P0 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/validation/final_validation.py` | geometry validation이 겹침/stub/protected corridor를 확인하지 않음 | `13_step9_validation.md §15.1` | P0 | 높음 | `rewrite` |
| `tests/unit/shapez_asteroid_v2/test_final_validation_contract.py` | skeleton leniency를 그대로 승인 | `13_step9_validation.md §15` | P2 | 높음 | `test-only` |

## recovery drift

| File | 관측 | 정본 참조 | 심각도 | 신뢰도 | 조치 |
|---|---|---|---|---|---|
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/corridor_opening.py` | recovery가 placement rollback, route 계획, trace 생성, state mutation을 한 파일에서 처리 | `11_step8_recovery.md`, `02_pipeline_control_flow.md §4.3` | P1 | 높음 | `split` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/routing/step4_corridor_recovery.py` | recovery entrypoint가 routing이 아니라 placement에 귀속 | `08_step4_routing.md`, `11_step8_recovery.md` | P1 | 높음 | `migrate` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/orchestration.py` | recovery attempt/context chain 상태가 없음 | `11_step8_recovery.md`, `03_data_schema_dto.md` | P1 | 높음 | `rewrite` |
| `django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/domain/enums.py` + 구현 전반 | trigger enum은 있으나 trigger별 복귀 경로 구현체 부재 | `02_pipeline_control_flow.md §4.3` | P1 | 높음 | `rewrite` |

## 유지해도 되는 부분

- `routing/connectivity.py`
  - read-only graph utility라 validation에서 계속 사용 가능
- `placement/placement_fsm.py`
  - state transition contract 자체는 비교적 정합

## 조사 보류

- `final_validation_failure` 이후 bounded recovery의 실제 orchestration path는 구현 부재라 현 단계에서는 “없음”으로 분류했다.
- `rollback/quarantine` lifecycle은 enum/FSM까지만 있고 end-to-end route/placement 통합 검증은 없다.
