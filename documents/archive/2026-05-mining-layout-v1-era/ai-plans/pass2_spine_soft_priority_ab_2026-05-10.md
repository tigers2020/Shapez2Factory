# Pass2 spine soft 우선순위 A/B 활용 플랜 (2026-05-10)

## 목적

[`07_step3_pass2_placement.md`](../../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md) §8 Pass2 spine을 **inner-first 정렬의 보수적 soft 우선순위**로만 활용한다. 현재 [`pass1_timeline_integration.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass1_timeline_integration.py)에서 spine 시드 카운트는 관측만 노출하고 있다 (Phase B). 본 wave는 그 시드를 **후보 정렬 키**로만 흘려서 ON/OFF A/B 비교가 가능한 형태로 한 단계 진행한다.

후보 풀·`try_commit_pass2_bundle` 게이트·extension 토폴로지 enum 순서 등 모든 의사결정 게이트는 **변경하지 않는다.**

## 정본·전제

- 정본: [`07_step3_pass2_placement.md`](../../Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md) §8.1·§8.3 — Pass1 결과 고정·내부 mineable 보강·route 확정 전 provisional commit.
- 횡단: [`12_protected_corridor.md`](../../Algorithm/mining_solver_cursor_sessions/12_protected_corridor.md) — Pass2 단계는 corridor가 hard로 승격되기 전이므로 정렬 변경은 안전.
- 직전 wave 종료: [`../checklist.md`](../checklist.md)「세션 대조 진척 요약 (2026-05-10) … wave 종료」.

## 범위

- **활용 깊이**: A. Soft 우선순위만 — spine 시드 인접 mineable 셀을 inner-first 정렬 결과 **앞쪽**으로 끌어오기.
- **ON/OFF**: 함수 인자 `pass2_spine_priority_enabled: bool = False`. 솔버 외부 호출은 always-OFF, 단위 테스트만 ON.
- 관측: `solver_summary["pass2_spine_priority_applied"]: bool` 한 줄 추가.

## 비범위

- B. Stub 방향 우선·C. monotone path 후보는 본 wave 후속 단계.
- 다른 우선순위 후보(Recovery trigger, §E TypedDict)는 별도 wave.
- 새 trace event·replay 이벤트 추가 없음.

## 변경 지점

### 1. 정렬 함수

[`placement/pass2_internal_placement.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass2_internal_placement.py)

- `mineable_inner_first_order(mineable_cells, asteroid_cells, *, priority_seeds=None)`로 시그니처 확장.
- `priority_seeds: frozenset[Coord] | None`이 주어지면, **inner / perimeter 분리 후 각 그룹 내에서** `priority_seeds`에 인접한 셀(맨해튼 1칸)을 그룹 선두로 끌어온다. 그룹 자체는 유지(inner > perimeter 원칙 보전).
- `priority_seeds=None`이면 기존 출력과 byte-equal.
- 같은 그룹 내 priority/non-priority 사이는 기존 좌표 정렬 키로 stable.

### 2. MVP runner 인자

같은 파일의 `run_pass2_internal_placement_mvp`에 `priority_seeds: frozenset[Coord] | None = None`를 추가하고 정렬 함수에 그대로 전달. 다른 흐름 변경 없음.

### 3. Timeline integration 배선

[`placement/pass1_timeline_integration.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/placement/pass1_timeline_integration.py)

- `integrate_pass12_placement_into_working_map`에 `pass2_spine_priority_enabled: bool = False` 인자 추가.
- ON일 때 이미 계산된 `spine_seeds`를 `frozenset(spine_seeds)`로 `run_pass2_internal_placement_mvp(..., priority_seeds=...)`에 전달.
- OFF면 `priority_seeds=None` (현재와 동일).
- `stats`에 `pass2_spine_priority_applied: bool` 추가.

### 4. Summary 계약

[`solver_pipeline/finalize.py`](../../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py) `apply_exception_summary_defaults`에 `pass2_spine_priority_applied: False` 기본값 추가. 정상 경로는 `**pass12_trace_fields` spread로 자동 노출.

## 테스트

[`tests/unit/shapez_asteroid/test_pass2_internal_placement.py`](../../../tests/unit/shapez_asteroid/test_pass2_internal_placement.py) 또는 `test_pass1_timeline_integration.py`에 회귀 4건:

1. **OFF identity** — `priority_seeds=None`일 때 정렬 결과가 기존 호출과 완전히 같다.
2. **ON soft priority** — 인공 mineable/asteroid/seed 셋업에서 시드 인접 셀이 inner 그룹의 선두로 이동하고, inner 셀이 perimeter 셀보다 여전히 앞이다.
3. **ON 결정론** — 같은 입력으로 두 번 호출 시 결과 동일.
4. **A/B summary** — `integrate_pass12_placement_into_working_map`을 OFF/ON으로 호출해 `pass2_spine_priority_applied` 토글 확인. 둘 다 stats가 dict로 정상 반환.

`build_solver_timeline`은 spine priority OFF만 사용하므로 본 함수 자체에 ON 케이스 회귀를 두지 않는다.

## A/B 비교 지표 (메모용)

같은 입력으로 ON/OFF에서 비교 가능 — 본 wave는 단언 외 데이터 수집은 하지 않는다.

- `pass2_internal_placements`
- `pass2_new_extractor_cells`·`pass2_new_extension_cells`
- `pass3_internal_transport_saved`
- `final_counts.transport_cells`·`final_counts.extractors`

## 검증

- 영향 구간: `python -m pytest tests/unit/shapez_asteroid/test_pass2_internal_placement.py tests/unit/shapez_asteroid/test_pass1_timeline_integration.py tests/unit/shapez_asteroid/test_mining_solver_stabilization.py`
- 전체 회귀: `python -m pytest tests/unit/shapez_asteroid/`
- 변경 파일에 `ruff check` / `mypy` / `black --check`.

## 롤백

- `priority_seeds=None` + `pass2_spine_priority_enabled=False` 디폴트로 본 변경은 기본 OFF. 회귀 발견 시 timeline integration의 ON 분기 한 줄 제거 또는 호출부 OFF 강제로 즉시 종료.

## 게이트

1. 본 플랜 사람 승인 → 본 MD를 정본으로 사용.
2. 코드 변경 → 영향 구간 회귀 → 변경 파일 lint.
3. [`../checklist.md`](../checklist.md)·[`../current_plan.md`](../current_plan.md) 진척 반영.
