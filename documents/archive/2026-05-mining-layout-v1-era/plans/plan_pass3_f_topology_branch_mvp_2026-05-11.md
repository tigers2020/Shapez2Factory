# Pass3 P3-F: Topology Branch Replacement MVP — 실행 플랜 (2026-05-11)

본 문서는 [P3-F 채팅 플랜](../../../c%3A/Users/hyper/.cursor/plans/p3-f_topology_branch_mvp_7eca188f.plan.md) 승인본 + 리뷰어 후속 권고(우선순위 정렬·`parallel_duplicate` 비활성 명시·`replacement_connected` 의미 명시)를 구현 게이트용 한국어 메모로 옮긴 것이다.
**솔버·검증 로직은 바꾸지 않는다.** 기존 P3-E3 guarded atomic 인프라 위에 **branch semantics layer**(detector + trace + commit alias)만 얹는다.

## 범위

- P3-E3 atomic candidate(DTO·검증·스왑·롤백) **재사용**.
- 상위에 **분기 후보 분류·probe 계측·commit alias**를 `p3f_*` 네임스페이스로 노출.

## 범위 밖

- STEP4 skeleton 재작성.
- P4 net-score 도입.
- 다중 branch 순차 commit (한 번에 branch 1개 원칙).
- Pass12 `placement_candidate_blocked_count` 실계측 (별도 티켓).

## Trace 키 계약 (`p3f_*` 네임스페이스)

### Detector

| 키 | 타입 | 정의 |
|---|---|---|
| `p3f_candidate_kind_count` | int (0–4) | 4종 라벨 중 참인 신호 개수. |
| `p3f_best_candidate_kind` | str | 결정적 우선순위(아래)로 최상위 1종 또는 `"none"`. |
| `p3f_candidate_kinds` | list[str] | 참인 라벨, **`P3F_KIND_PRIORITY_ORDER` 기준 정렬**(알파벳 X). |
| `p3f_candidate_internal_cells` | int | `len(removed_transport_cells ∩ asteroid)` — **단일 정의**. |
| `p3f_candidate_mineable_freed` | int | `len(removed_transport_cells ∩ mineable)`. |
| `p3f_candidate_reuse_ratio` | float (0–1, 6자리 반올림) | `|removed ∩ trunk_cells| / max(1, |removed|)`. |
| `p3f_candidate_score_tuple` | list[number] | `[internal_delta, reuse_ratio, mineable_freed, route_cell_delta]`. |
| `p3f_parallel_duplicate_inactive_reason` | str \| null | greedy 경로가 없어 `parallel_duplicate_branch` 검출이 비활성일 때 `"greedy_paths_unavailable"`. 활성 시 `null`. |

#### `p3f_best_candidate_kind` 결정적 우선순위 (튜플 순서)

1. `mineable_heavy_branch`
2. `long_perimeter_detour`
3. `parallel_duplicate_branch`
4. `low_reuse_branch`

근거: mineable 회수가 직접 throughput 영향, detour는 길이 절감, parallel duplicate는 trunk 공유 기회, low reuse는 신호 강도가 가장 약한 보조 라벨.

#### 라벨 판별

- `mineable_heavy_branch`: `(removed ∩ mineable) / max(1, removed)` ≥ `P3F_MINEABLE_HEAVY_RATIO_MIN`.
- `long_perimeter_detour`: `sum_gr_len ≥ sum_lex_len * P3F_LONG_DETOUR_RATIO_MIN`.
- `parallel_duplicate_branch`: per-stub greedy 경로 쌍 중 (1) 동일 trunk cell에 도달 + (2) endpoint Manhattan ≤ `P3F_PARALLEL_ENDPOINT_MANHATTAN_MAX` + (3) `shared_cells / max_len ≤ P3F_PARALLEL_OVERLAP_RATIO_MAX`. **MVP 단계는 greedy 경로 미공급이 기본**이므로 라벨 자체는 사실상 비활성이고, 비활성 사유는 `p3f_parallel_duplicate_inactive_reason`에 명시.
- `low_reuse_branch`: `(removed ∩ trunk_cells) / max(1, removed)` ≤ `P3F_LOW_REUSE_RATIO_MAX`.

### Replacement probe

| 키 | 타입 | 정의 |
|---|---|---|
| `p3f_replacement_connected` | bool \| null | **P3-E3 precheck 통과 여부**: `dto.attempted ∧ dto.precheck_passed ∧ dto.rejected_reason is None`. 순수 연결성 단독 probe가 아니라 “lex + greedy probe가 모든 stub에 대해 성공했고 DTO가 reject 사유를 갖지 않음”을 의미한다. 다운스트림 연결성은 `_p3e3_validate_candidate_transport_map`에서 확정되며 그 결과는 reject 경로로 반영된다. |
| `p3f_fixed_output_stub_preserved` | bool | `fixed_output_stubs ⊆ candidate_transport_cells`. |
| `p3f_hard_protected_preserved` | bool | hard corridor ⊆ candidate transport. |
| `p3f_internal_transport_delta` | int | `candidate_internal − baseline_internal` (둘 다 `asteroid` 교집합 실측). |
| `p3f_route_cell_delta` | int | `dto.candidate_route_length − dto.baseline_route_length`. |
| `p3f_route_cell_delta_within_budget` | bool | 기존 `MAX_ROUTE_LENGTH_RATIO` 기준. |
| `p3f_replacement_search_mode` | str | MVP 고정 `"p3e3_lex_per_stub"`. |
| `p3f_replacement_expanded_nodes` | int \| null | router가 카운터를 노출하지 않으면 `null`. |
| `p3f_replacement_search_ms` | int | `_p3e3_run_atomic_candidate_phase` `perf_counter` 밀리초. |

### Atomic commit alias

| 키 | 타입 | 정의 |
|---|---|---|
| `p3f_committed` | bool | `guarded_committed_outcome`와 동일. |
| `p3f_transport_cells_added` | int | `len(dto.added_transport_cells)`. |
| `p3f_transport_cells_removed` | int | `len(dto.removed_transport_cells)`. |
| `p3f_internal_transport_saved` | int | 기존 `pass3_internal_transport_saved` mirror. |
| `p3f_commit_reason` | str \| null | 성공 시 `"normal_gain"`. |
| `p3f_rejected_reason` | str \| null | 매핑 테이블 결과. |
| `p3f_rejected_reason_raw` | str \| null | 매핑 실패 시 원본 보존. |

## 구현 파일

- 신규: `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass3/pass3_f_branch_candidate.py`
  - 순수 함수, 의존: `foundation.geometry`, `foundation.constants`, `pass3_e3_guarded_dto`.
- 수정: `pass3/pass3_transport.py` — atomic 단계 perf counter, DTO 후 `p3f_*` 병합.
- 수정: `foundation/constants.py` — `P3F_*` 임계 상수.
- 수정 없음: P3-E3 본체·검증·롤백 로직.

## 파이프라인·UI 노출

- `solver_pipeline/pass3.py`의 `p3_trace → pass3_summary` 포워딩 루프는 이미 `p3e2_/p3e3_` prefix를 받는다. `p3f_` prefix를 추가한다.
- `views.py` keys 튜플은 P3-F MVP에서 변경하지 않는다(추가 노출은 후속 UI 티켓).

## 테스트

- 신규: `tests/unit/shapez_asteroid/test_pass3_f_topology_branch.py`
- 기존 `test_optimization_baseline.py`는 변경 없음 (P3-F 키는 새로 추가되어 기존 단정에 영향이 없다).

## 검증 명령

```text
python -m pytest tests/unit/shapez_asteroid/ -q
ruff check .
mypy .
black --check .
```
