# STEP4 / Pass2 goal·failure diagnostics (2026-05-12)

## 개요

- Pass2 `first_route`에서 `exterior_margin_cell_count == 0` → 빈 goal trace와 STEP4 요약 `failure_reason`이 `mixed_transport_kind`로 과대표시되는 문제를 **분리**해 감사·수정한다.
- **비목표**: Pass3/P4 동작 변경, Pass12 stub-route **알고리즘** 변경(설정 키 문서화만).

## 로그 사실 (`latest.ndjson`, `run_id=8c733713ede1`)

- `step4_partial_failure` → Pass3 `step4_not_committed`, P4 `pass3_not_eligible`.
- Pass2: `first_route: 12`, `exterior_margin_cell_count: 0`, `final_goal_count: 0`.
- Pass12 stub-route: `disabled_by_flag: true`, `attempted_count: 0` → **설정**으로 해석(코드 결함 단정 아님).
- STEP4 detail: `existing_trunk_goal_count` 큼, `last_error: no_route_exhausted`, 요약 `failure_reason: mixed_transport_kind` 불일치.

## 설정 키 정본

- `SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY`: 느슨한 회전 등 별도 경로. 기본 OFF.
- `SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY`: merged-seed stub-route recovery. 기본 ON. NDJSON `pass12_stub_route_recovery_*`는 이쪽.

## 가설

- **Pass2**: `first_route`이고 외부 마진 0·goal 0이면 `no_exterior_margin_for_probe`로 명시(Outcome B). universe/`is_external` 버그면 Outcome A로 별도 수정.
- **STEP4 분류기**: `stub_cell_role_ok`가 `inferred` 등에서 False → `mixed_transport_kind`가 **탐색 실패보다 먼저** 선택되는 순서 문제. 라우팅 동작은 변경하지 않고 **분류 순서·enum 보강**만.

## 테스트

1. margin 있음 → `final_goal_count > 0`
2. `first_route` + margin 0 + 빈 goal → `no_exterior_margin_for_probe`
3. goal > 0 + `last_error=no_route_exhausted` → `failure_reason != mixed_transport_kind`
4. 진짜 역할 불일치 → `mixed_transport_kind`

## 검증

`python -m pytest tests/unit/shapez_asteroid/test_step4_remaining_partial_failure_diagnostics.py tests/unit/shapez_asteroid/test_step4_route_failure_diagnostics.py tests/unit/shapez_asteroid/test_step4_first_route_goal_set.py` → `ruff check .` → `mypy .` → `black --check .`
