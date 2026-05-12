# 목표: PlacementCommitState와 merged existing seed 예외 정합

**선행 감사(권장):** [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md) — 네 상태 전이·정본 대비 읽기 전용 표를 채운 뒤 본 문서의 코드/문서 선택을 확정한다.

## 배경

- 정본: `08_step4_routing.md` §9.6, `03_data_schema_dto.md` §B — Pass2 직후 `PROVISIONAL_PLACED`, STEP4 성공 후 `ROUTED_CONFIRMED`.
- 구현: `pass12_merged_layout_seed.seed_pass12_scratch_from_merged_existing`에서 기존 트렁크 재사용 시 **STEP4 전에** `ROUTED_CONFIRMED`를 부여할 수 있다(독스트링에 “STEP4 treats them as finalized bundles” 명시).

## 현재 상태

- 의도적 최적화/예외이나, 엄격한 §9.6 문장과 읽기 충돌이 난다.

## 목표 상태

- **문서**에 “merged seed / preserve layout” 예외 절을 추가하거나,
- **코드**에서 항상 `PROVISIONAL_PLACED`로 두고 STEP4에서 no-op 확정으로 `ROUTED_CONFIRMED` 승격(동작 동치 유지 여부 검증).

## 작업 항목

1. merged seed 경로에서 STEP4가 실제로 no-op인지·라우팅 실패 시 FSM이 어떻게 되는지 시나리오별 표 작성.
2. `unfinalized_placement_count` / Pass3 게이트와의 상호작용 확인.
3. 선택안 A/B에 대한 테스트 최소 1건.

## 검증

- `placement_commit`·STEP4 통합 테스트로 상태 전이 고정.

## 위험

- 상태를 PROVISIONAL로만 바꾸면 Pass3 eligibility·guard 경로가 달라질 수 있음 — 전 구간 회귀 필요.

## 참고 코드

- `placement/pass12_merged_layout_seed.py`
- `placement/placement_commit.py`, `step4/step4_merge_routing.py`
