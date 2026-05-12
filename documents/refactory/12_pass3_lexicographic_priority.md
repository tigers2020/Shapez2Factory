# 목표: Pass3 사전순 우선순위와 §10.4·`lexicographic_router` 정합 유지

## 배경

- 정본: `09_step5_pass3_transport.md` §10.4 — 튜플 순서: internal → opportunity → route cost → congestion → turn → path length → tie-break 좌표.
- 구현: `routing/lexicographic_router.py` `_step_deltas` / `_add_lex_prefix`.

## 현재 상태

- 구현이 정본과 대체로 일치하나, 축 의미(특히 congestion·기존 transport 재사용 시 route_step 클램프)가 바뀌면 **의사결정 순서**가 바뀐다.

## 목표 상태

- 튜플 축을 **단일 소스**(정본 표 또는 코드 enum 순서)로 두고, 변경 시 `search_mode`·`optimality_guarantee`·trace에 tie-break 키를 남긴다(§10.4 후반).

## 작업 항목

1. `LexTuple` / `_step_deltas` 필드 순서를 §10.4 표와 1행 표로 매핑해 `refactory` 또는 `Algorithm` 쪽에 고정.
2. weighted A* / fallback 경로가 있다면 §10.6과 동일하게 `search_mode`·`fallback_reason` 계약 유지.
3. 회귀: 동일 입력에서 path·trace 우선순위 결정론.

## 검증

- 단위: 소형 그리드에서 기대 path 고정.

## 참고 코드

- `routing/lexicographic_router.py`, `routing/lexicographic_router_contracts.py`
- `pass3/pass3_e2_shadow.py`, `pass3/pass3_e3_guarded_lex_collect.py`
