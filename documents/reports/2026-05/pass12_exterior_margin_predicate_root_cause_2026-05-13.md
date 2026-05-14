# Pass2 외부 마진 0·`is_external` 샘플 관측 — 루트 코즈 (코드 계약 정리)

**상태**: REPORT (정본 아님)  
**날짜**: 2026-05-13

## 요약

`exterior_margin_cell_count == 0`이면서 `sampled_neighbor_outside_universe_count > 0`이고 `is_external_true_neighbor_sample_count == 0`인 패턴은, **구현상 모순이 아니라** `final_validation._external_predicate`와 `step4_goal_trunk_seed.exterior_margin_cells`의 계약에 맞을 수 있다.

## 계약

1. **`is_external(n)`** ([`final_validation._external_predicate`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/validation/final_validation.py)): 장비 hull(또는 mineable bbox)에 동적 margin을 더한 **축 정렬 사각형 밖**이고 `x != 0`일 때만 True.
2. **`exterior_margin_cells`**: routing universe(셀 키 ∪ mineable ∪ asteroid ∪ `universe_extra`)의 `x != 0` 셀 `c`에 대해, 4-이웃 중 하나라도 `is_external(n)`이면 `c`를 포함.

## 관측 해석

- 이웃 좌표가 **universe 밖**(셀 dict에 없음)이어도, 그 좌표가 여전히 **expanded hull( predicate bbox ± margin ) 안**이면 `is_external`은 False다. 즉 “그리드 상 빈 칸”이 “게임 바깥”이 아니다.
- Pass2 진단 샘플([`pass12_route_probe._build_pass2_external_margin_diagnostic`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_route_probe.py))의 `sampled_neighbor_shell_breakdown`으로, 샘플 이웃이 셸 안/밖/`x==0`인지 구분 가능하다.

## 파생 증상

- `trunk_seed_candidate_count == 0`: ELA `trunk_seed_cell_union`이 비었거나 main trunk 없음.
- `raw_goal` 공집합 → `pass2_probe_goal_count == 0`, `rejected_reason == no_exterior_margin_for_probe` (첫 라우트·margin·hint·`trunk_now` 모두 빈 경우).

## 보존 드롭 `NO_MATCHING_STUB`

분류기([`pass12_merged_layout_seed._classify_preserve_drop_reason`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass12_merged_layout_seed.py))는 “인접 stub 자리 없음 + BFS로 같은 종류 transport가 1홉 이상”일 때 `NO_MATCHING_STUB`을 쓴다. **이름과 실제 블로커(목표 집합 공집합·경로 탐색 실패 등)가 다를 수 있어**, trace 전용 `preserve_drop_blocker` / `preserve_drop_detail` 보강이 필요하다(구현 참조).

## 리플레이 카운터

- `map_timeline_built.timeline_frame_count`: `build_map_timeline` 단계 수(소수).
- `solver_summary.replay_event_count` 등: `solver_trace.trace_event` 누적 + stride `replay_frame` — **별도 계층**이다. `solver_summary.trace_frame_counter_glossary`(finalize)로 소비자 혼동 완화.
