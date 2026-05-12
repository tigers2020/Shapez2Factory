# Plan: dead code cleanup sequence refactor (2026-05-01)

관련 리서치: [research_dead_code_cleanup_2026-05-01.md](./research_dead_code_cleanup_2026-05-01.md)

원본 요청 요약: 런타임에서 이미 대체된 죽은 경로와 중복 solve 로직을 정리하고, 안전한 순서로 삭제 가능한 파일까지 줄인다.

## 구현 접근

1. [django_apps/shapez_solver/services/solver_service.py](../../../../../django_apps/shapez_solver/services/solver_service.py) 와 [factory_throughput_service.py](../../../../../django_apps/shapez_solver/services/factory_throughput_service.py) 사이의 공통 solve 파이프라인을 공용 helper 로 추출한다.
2. 뷰와 신규 테스트가 이미 사용하는 `FactoryThroughputService` 를 주 경로로 유지하고, 기존 `SolverService` 는 다음 둘 중 하나로 축소한다.
   - 안전안: 공용 helper 를 감싸는 최소 호환 wrapper 로 유지한다.
   - 삭제안: 저장소 내 테스트를 모두 새 서비스 기준으로 옮긴 뒤 파일 자체를 삭제한다.
3. 이미 삭제된 [graph_builder.py](../../../../../django_apps/shapez_solver/services/graph_builder.py) 의 남은 코드/테스트 참조가 없는지 정리한다.
4. 중복 테스트는 새 서비스 기준으로 흡수하고, 죽은 계약 테스트는 제거하거나 이름을 바꿔 현재 계약을 정확히 반영한다.

## 승인 포인트

- `solver_service.py` 를 완전히 삭제할지, 아니면 최소 호환 shim 으로 남길지 결정이 필요하다.
- 외부 import 호환 리스크를 낮추려면 기본값은 안전안(shim 유지) 이다.
- 사용자가 "파일 자체 삭제"를 우선하면 삭제안으로 갈 수 있지만, 그 경우 테스트와 import 경로가 함께 바뀐다.

## 호환성 기준

- `/api/solver/solve/` 응답 계약은 유지한다.
- 현재 추가된 `target_count`, `base_demands`, 그래프 target quantity 동작은 유지한다.
- planner/operation replay 검증 로직은 한 곳에서만 유지되도록 만들어야 한다.

## 검증

- `python -m pytest tests/unit/shapez_solver/test_factory_throughput_service.py`
- `python -m pytest tests/unit/shapez_solver/test_solver_service.py`
- `python -m pytest tests/unit/shapez_core/test_shape_code_parser.py`
- `python -m pytest tests/integration/api/test_solver_api.py`
- `python -m pytest tests/integration/web/test_web_smoke.py`
- `python -m ruff check .`
- `python -m mypy .`
- `python -m black .`
