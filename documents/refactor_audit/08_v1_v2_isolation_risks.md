# v1 / v2 Isolation Risks

## 현재 상태

- good: `tests/unit/asteroid_lab/test_service_import_boundaries.py`가 old mining solver namespace 문자열을 금지한다.
- risk: live repo에는 `django_apps/shapez_solver`와 `django_apps/asteroid_lab`가 동시에 존재하고, 둘 다 `SolverRun`, `PatternTemplate` 같은 명사를 사용한다.
- risk: canonical 문서는 `shapez_asteroid` / `asteroid_mining_layout_v2`를 기준으로 쓰였지만 live app은 `asteroid_lab`다.

## risk matrix

| File / area | Isolation risk | Root cause | Severity | Confidence | Action |
|---|---|---|---|---|---|
| `tests/unit/asteroid_lab/test_service_import_boundaries.py` | namespace 금지가 substring 수준 | graph-level allowed-edge 검증 없음 | `P2` | High | `test-only` |
| `django_apps/asteroid_lab/models.py` vs `django_apps/shapez_solver/models.py` | `SolverRun`, `PatternTemplate` 명사 중복 | domain vocabulary collision | `P1` | Medium | `isolate` |
| canonical docs vs live tree | v2 문서가 현재 lab shell 위에 직접 대응되지 않음 | migration map 부재 | `P0` | High | `freeze` |
| `django_apps/asteroid_lab/services/project_service.py` | docstring이 old v1/v2 solver internals 비사용을 강조하지만 live semantic 경계 자체가 애매 | defensive wording이 구조를 대체 | `P2` | Medium | `rewrite` |

## 실제로 확인된 것

- `django_apps/asteroid_lab` 내부 다중 파일 SCC 없음
- `django_apps/asteroid_lab`에서 `django_apps.shapez_asteroid`, `asteroid_mining_layout_v1`, `asteroid_mining_layout_v2` runtime import는 발견되지 않음

## 그러나 남는 위험

1. 추후 canonical solver migration 시 `asteroid_lab`가 임시 shell인지 long-lived app인지 불명확하다.
2. 모델 명사 충돌 때문에 serializer, admin, migration, docs에서 용어 오해가 발생하기 쉽다.
3. 문서가 가정하는 v2 package가 live repo에 없어서, isolation refactor 순서가 뒤집히기 쉽다.

## 권장 조치

- phase 1에서 `asteroid_lab`의 위치를 명확히 선언
  - option A: inspection/replay sandbox로 고정
  - option B: canonical solver runtime의 전초 패키지로 승격
- 어느 쪽이든 `shapez_solver`와 vocabulary collision table을 먼저 만든다.
