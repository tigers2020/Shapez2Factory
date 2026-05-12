# 목표: Pass1/Pass2 cheap escape·probe가 route/occupied에 오염되지 않도록 유지

## 배경

- 정본: `08_step4_routing.md` §9.2 — `cheap_transport_escape_exists()`가 쓴 **임시 path**는 trunk seed·goal set에 넣지 않는다.
- 구현: `placement/pass12_route_probe.py` `bundle_route_probe_or_reject` — Pass1 전용 void envelope는 **맵에 belt/pipe로 커밋하지 않음**을 독스트링으로 명시한다.

## 현재 상태

- 의도는 코드에 반영되어 있으나, 신규 probe 종류 추가 시 동일 불변식이 깨지기 쉽다.

## 목표 상태

- 모든 placement 전 probe 경로가 **(1) trace 전용** 또는 **(2) 명시적 allowed_cells로만** 존재하고, `working_map` 반영 전 **commit 경로와 분리**된다는 것을 계약으로 고정한다.

## 작업 항목

1. `probe_*` / `cheap_escape` 호출부 전수: `transport_cells`·`blocked_cells` 인자가 실제 커밋 맵과 동기인지 확인.
2. STEP4 `trunk_seed`·goal 조립 코드와의 **데이터 흐름 다이어그램** 1장(문서).
3. 회귀 테스트: cheap escape 성공 후에도 해당 void가 `role=belt|pipe`로 남지 않음.

## 검증

- 단위: Pass1 envelope / Pass2 uncertain 경로별 스냅샷.

## 위험

- probe와 commit을 공유하는 버퍼 재사용 시 실수 변이.

## 참고 코드

- `placement/pass12_route_probe.py`, `placement/pass12_bundle_commit.py`
- `routing/route_probe.py` (`probe_stub_cheap_escape_to_external_detail` 등)
