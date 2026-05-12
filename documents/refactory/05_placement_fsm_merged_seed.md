# 목표: PlacementCommitState와 merged existing seed 예외 정합

**선행 감사(권장):** [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md) — 네 상태 전이·정본 대비 읽기 전용 표를 채운 뒤 본 문서의 코드/문서 선택을 확정한다.

## 배경

- 정본: `08_step4_routing.md` §9.6, `03_data_schema_dto.md` §B — Pass2 직후 `PROVISIONAL_PLACED`, STEP4 성공 후 `ROUTED_CONFIRMED`.
- 구현(이전): `seed_pass12_scratch_from_merged_existing`에서 기존 트렁크 재사용 시 **STEP4 전에** `ROUTED_CONFIRMED`를 부여할 수 있었다.

## 현재 상태

- **코드 회귀(2026-05-12):** merged/preserve seed는 **항상** `PROVISIONAL_PLACED`만 기록하고, `ROUTED_CONFIRMED`는 STEP4(필요 시 stub∈trunk **no-op route commit**)에서만 승격한다 — §9.6 처리 규칙 1–2와 정렬.

## 목표 상태

- 코드가 §9.6 기본안을 따른다(merged seed도 Pass12 직후 `PROVISIONAL_PLACED`만). 본 문서는 감사·위험 메모로 유지한다.

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
