# 목표: `trunk_load`를 1차 합산 관측으로 유지(hard gate 아님)

## 배경

- 정본: `08_step4_routing.md` §9.4, `03_data_schema_dto.md` §3.6 — 1차는 **rated max와 비교하지 않고** 합산·trace; hard constraint는 후속 플래그.

## 현재 상태

- `step4_trunk_load.py` 및 계약 버전(`TRUNK_LOAD_CONTRACT_VERSION`)으로 의도가 문서화되어 있다.

## 목표 상태

- 용량 gate를 켤 때에도 **STEP4 commit 조건**과 **trunk_load 필드**의 책임 분리를 유지한다(검증은 §15.3·STEP4 쪽과 중복되지 않게).

## 작업 항목

1. `trunk_load`를 읽어 라우팅을 거절하는 분기가 생기면 코드 리뷰 게이트에 올린다.
2. `p2c_metrics` 병합 시 계약 키 보호(`_TRUNK_LOAD_CONTRACT_P2C_SAFEGUARD_KEYS`) 정책 유지 여부 점검.
3. Final validation과의 역할 분담 표(한 표).

## 검증

- `test_step4_trunk_load_contract` 등 기존 계약 테스트 유지·갱신.

## 참고 코드

- `step4/step4_trunk_load.py`, `finalize.py` (summary 병합)
