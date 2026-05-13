# 10 — STEP 6: Reclaim loop (§12, P4)

> **출처**: [`Shapez2 Asteroid Mining Solver logic.md`](../Shapez2%20Asteroid%20Mining%20Solver%20logic.md)에서 분할한 Cursor 구현 세션용 조각이다.

> **의존성**: 09

---

## 12. STEP 6 — Reclaim Placement Loop

### 12.1 목적

Pass3가 내부 transport를 줄여 확보한 공간을 실제 placement 개선으로 연결한다.

v3의 문제는 다음이었다.

```text
Pass3가 내부 transport를 줄였지만,
Reclaim loop의 incremental route가 다시 내부 transport를 늘려 Pass3 최적화를 역행할 수 있었다.
```

v4에서는 Reclaim loop에 **internal transport budget**을 추가한다.

```text
Pass3 reroute
→ internal_transport_saved 계산
→ reclaimed_cells / freed_candidate_cells 계산
→ zone map 갱신
→ 신규 extractor + extension 후보 scan
→ incremental routing
→ internal transport budget 검사
→ capacity/connectivity validation
→ 필요 시 bounded post-reclaim Pass3 rerun
```

---

### 12.2 Reclaim candidate 조건

§4.2의 루프 요약과 달리, 본 절이 **후보 채택·gain·누적 internal transport budget의 규범(canonical) 정의**다.

```text
DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD = 1.5   # gain / additional_route_cost 최소 비율 (튜닝 범위 예: 1.2 ~ 2.5)
```

**`gain` · `additional_route_cost` 단위(정본)**: 게이트를 단순화하기 위해 분자·분모를 한 쌍으로 고정한다. **물리 차원이 엄격히 동일하지 않을 수 있음**을 전제로, 아래 **MVP 구현 표준**과 `DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD`는 **경험적 튜닝**으로 읽는다(값을 바꾸면 함께 재튜닝).

```text
- gain(MVP): 신규 shadow bundle이 가져오는 **기대 채굴 슬롯 증가분**을 **무차원 스칼라(slots 수)** 로 둔다(구현 상수 `RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS` 등). trace에는 필요 시 expected_output/min 환산값을 **추가**로 남긴다.
- additional_route_cost: **incremental route 전체**(§11.3: **fixed output stub 셀 포함**, stub는 “cost 0 고정”이 아니며 RouteZone·KIND 보정을 **합산에 포함**한다)에 대한 **RouteZone 기반 route cost 합**(§11.1·§11.2). trace에는 필요 시 `route_cost_including_stub` / `route_cost_after_stub`로 분해해 기록해 튜닝을 돕는다. capacity penalty는 본 ratio에 넣지 않고 STEP 4·검증에서 별도 처리.
```

**`gain_ratio`(MVP)**: `gain / additional_route_cost` = “**slots 대비 RouteZone 비용 합**”의 비율이다. **무차원 물리 비율이 아니다.** 정규화된 무차원 비율로 바꾸는 후속 설계가 생기면 본 절·상수·테스트를 함께 갱신한다.

**`pass3_internal_transport_saved` · 내부 transport 스냅샷 정렬(정본)**: `pass3_internal_transport_saved`는 **STEP 5 Pass3 성공 커밋 직후** 레이아웃에서 산출한다. `baseline_internal_transport_at_reclaim_entry`(§12.5)는 **Reclaim loop 진입 직전** 스냅샷이다. **두 값 모두** “Reclaim이 아직 아무 commit도 하기 전” 동일 물리 시점의 transport를 기준으로 하므로, **STEP 5 직후 ~ Reclaim 진입 사이**에 transport를 바꾸는 처리(예: `cascade_corrective_recovery`, 수동 repair)가 있었다면 **Pass3 절약분을 그 시점 레이아웃으로 재측정**해 `pass3_internal_transport_saved`를 갱신하거나, 동일 스냅샷에서 `pass3_internal_transport_saved`와 `baseline_internal_transport_at_reclaim_entry`의 **내부 transport 집계 정의를 동일 함수**로 맞춘다. §12.2 budget 수식의 `pass3_internal_transport_saved`와 §12.5·rerun 검증의 `net_internal_transport_saved_after_reclaim` 기준선이 **서로 다른 시점 레이아웃**을 가리키면 안 된다.

| 필드 | 의미(집계 종류) | 주 용도 |
| --- | --- | --- |
| `pass3_internal_transport_saved` | Pass3 전후 대비 **절약한 내부 transport 칸 수(델타)** | §12.2 reclaim internal transport **budget** 상한·`allowed_internal_spend` |
| `baseline_internal_transport_at_reclaim_entry` | Reclaim 직전 레이아웃의 **절대** 내부 transport 칸 수 | §12.5 `net`·post-reclaim Pass3 rerun **게이트** 기준선 |

동일 물리 시점 레이아웃을 보되, 위 둘은 **서로 다른 의미의 수치**이므로 숫자가 같아지는 것이 아니다.

신규 placement 후보는 다음 조건을 만족해야 한다.

```text
[ ] reclaimed 또는 여전히 비어 있는 mineable cell 위에 있다.
[ ] final_route_cells 위에 올라가지 않는다.
[ ] hard_protected corridor를 침범하지 않는다.
[ ] output stub를 만들 수 있다.
[ ] incremental routing이 가능하다.
[ ] capacity를 초과하지 않는다.
[ ] gain / additional_route_cost >= DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD (튜닝 시 상수명 유지·값만 변경).
[ ] incremental route length ratio가 STEP 6 제한 이내다.
[ ] 누적 `incremental_internal_transport_added`가 Pass3 절약분 budget 이내다(아래 누적 규칙).
```

권장 budget:

```text
MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO = 0.35
MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS = 1  # 튜닝: 1~2 cells
```

내부 transport budget은 **Reclaim loop 한 번의 실행 동안 누적**한다. 아래는 **commit 전 평가**와 **commit 성공 후 누적 갱신**을 분리한다.

```python
# 1) 후보 평가 (commit 전)
incremental_added = compute_incremental_internal_transport(candidate)
projected_total = total_reclaim_internal_added_so_far + incremental_added

# pass3_internal_transport_saved > 0 만 절약분으로 본다. == 0 또는 < 0(STEP 5 실패·보정으로 내부 transport가 늘어난 경우)은 동일 분기.
base_spend = floor(pass3_internal_transport_saved * MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO)
allowed_internal_spend = (
    base_spend if pass3_internal_transport_saved > 0
    else MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS
)

accept_reclaim = (
    projected_total <= allowed_internal_spend
    and (
        pass3_internal_transport_saved <= 0
        or (pass3_internal_transport_saved - projected_total) > 0
    )
)

# 2) commit 성공 시에만 누적치 갱신
if accept_reclaim and commit_succeeds:
    total_reclaim_internal_added_so_far = projected_total
```

둘째 줄은 `pass3_internal_transport_saved > 0`일 때만 “Reclaim 누적 후에도 Pass3 절약분이 남는가”(`net_internal_transport_saved_after_reclaim`과 동일 집계 정의)와 동치다.
`pass3_internal_transport_saved <= 0`(0 또는 음수)이면 **net 조건을 적용하지 않는다**(바닥 허용분만으로 전멸하는 모순 방지, §v5 Major 4). 음수는 assert로 막기보다 **절약분 없음과 동일**하게 위 분기로 처리한다.

`pass3_internal_transport_saved <= 0`인 경우에도 `allowed_internal_spend`가 0이 되면
모든 incremental 내부 경유가 금지되어 reclaim이 전멸할 수 있다. 위 **최소 바닥값**은 누적 한도가 0이 되지 않게 한다.

즉, Pass3가 내부 transport를 10칸 줄였으면 Reclaim incremental route는 기본적으로 3칸까지만 내부 transport를 다시 쓸 수 있다.

---

### 12.3 Reclaim 이후 zone map 갱신

Reclaim loop는 Pass3 당시의 zone map을 그대로 쓰면 안 된다. 신규 extractor/extension이 배치되면 zone classification이 바뀐다.

```text
Reclaim candidate provisional commit 후:
- 신규 extractor/extension cells → BLOCKED
- 신규 output stub → FIXED_STUB
- 신규 incremental route cells → zone 분류(아래). §14.2.1 **candidate_corridor → soft_protected** 승격 규칙과 동일하게,
  “replacement 검증(§14.3)까지 통과한 뒤 commit된 transport”는 **soft_protected**로 올리고,
  그 외 **일회성 probe·미검증 shadow**는 candidate_corridor로만 남긴다(§14.2.1 폐기 규칙 적용).
- 기존 placement candidate 중 점유된 셀 → candidate set에서 제거
```

**`FINAL_ROUTE` vs `SOFT_PROTECTED` (STEP 6 incremental)**:

```text
- 해당 incremental route segment가 STEP 4·Pass3와 동일하게 “최종 확정 trunk/연결 통로”로 취급될 때 → FINAL_ROUTE(또는 구현 명칭 final_route_cells에 합류).
- 위 soft 승격 조건을 만족한 corridor(§14.3 atomic replace 전제) → SOFT_PROTECTED. Reclaim에서도 **corridor를 비우기 전 replacement 선계산** 원칙은 STEP 4·recovery와 동일하다(§14.3).
```

구현 규칙:

```python
route_zone_map = rebuild_route_zone_map(
    mineable_cells=mineable_base,
    committed_placements=all_committed_placements,
    final_route_cells=final_route_cells,
    fixed_output_stubs=fixed_output_stubs,
    hard_protected_corridors=hard_protected_corridors,
    soft_protected_corridors=soft_protected_corridors,
)
```

incremental routing은 항상 **갱신된 zone map**을 사용한다.

---

### 12.4 Reclaim loop에서 route 제거 규칙

`route_cells_pass를 mineable_cur에서 제거`하는 규칙은 여기서 적용한다.

```text
Reclaim placement scan 전:
mineable_cur = mineable_base - final_route_cells - hard_protected_corridors - soft_protected_corridors - all_committed_placements
```

`soft_protected_corridors`는 §14.3 replacement·atomic replace로 해제되기 전까지 **mineable 후보에서 제외**한다(§18.2와 동일). 해제된 셀만 `mineable_cur`에 다시 포함된다.

단, soft_protected_corridor는 Pass3 또는 recovery가 replacement route를 성공적으로 검증하면 해제 가능하다.

#### 12.4.1 `soft_protected`와 `mineable_cur` 밀집 데드락 (MVP 탈출)

신규 placement는 `mineable_cur` 위에 서야 하고, `soft_protected_corridors`는 replacement 검증(§14.3) 전까지 mineable에서 제외된다. **밀집 소행성**에서는 “후보를 올릴 mineable”과 “replacement 없이는 못 비우는 soft”가 동시에 막혀 **후보 생성이 영구적으로 0**인 구성이 이론상 가능하다.

**MVP 정본(탈출)**: §14.3 **atomic replace로 replacement route가 성립할 때만** soft를 해제·재탐색한다. **replacement 없이 soft를 무시하거나 mineable 배제를 임시로 푸는 relax는 하지 않는다.** 해당 경우 Reclaim loop는 §12.6대로 **후보 없음·개별 reject로 종료**하고, 이미 연결된 known-good 레이아웃을 유지한다. solver 종료 등급은 §4.4(예: PARTIAL_SUCCESS)와 hard invariant(§15.1–15.3)를 따른다.

**비MVP(후속 옵션, 정본 밖 설계)**: 상위 **STEP 4 소프트 풀 재협상**(recovery·cascade)으로 soft 점유를 줄인 뒤 동일 solve에서 Reclaim을 다시 시도하는 등 — 채택 시 별 개정으로 §4·§14와 attempt 예산을 함께 적는다.

---

### 12.5 Post-reclaim Pass3 rerun 조건

Reclaim 후 내부 transport가 budget 이내이지만 여전히 개선 여지가 있으면 Pass3를 한 번만 재실행할 수 있다.

```text
post-reclaim Pass3 rerun 조건:
- reclaim placement가 1개 이상 commit됨
- incremental_internal_transport_added > 0
- net_internal_transport_saved_after_reclaim > 0 — **의미는 아래 “진입 시점”**
- 소행성 1회 solve 기준 MAX_POST_RECLAIM_PASS3_RERUNS 미도달(§4.2)
```

**STEP 7 게이트 평가 시점(정본)**: 위 목록·`net > 0`·`MAX_POST_RECLAIM_PASS3_RERUNS`는 **Reclaim placement loop(STEP 6) 전체가 끝난 뒤**, **P4 스테이지(STEP 6+STEP 7 블록)를 한 번 빠져나가기 직전**에 **한 번만** 평가한다. Reclaim **iteration마다** rerun을 시도하지 않는다. `MAX_POST_RECLAIM_PASS3_RERUNS`는 §4.2대로 **solve 전역 lifetime**이며 iteration과 무관하다.

**`net_internal_transport_saved_after_reclaim > 0` (rerun 진입 vs 사후)**: 목록의 `net > 0`은 **Pass3 rerun 블록을 실행하기 전**에 평가한다. 값은 **`baseline_internal_transport_at_reclaim_entry`(Reclaim loop 진입 직전 스냅샷)** 대비, **Reclaim loop가 끝난 직후·rerun 이전**에 재측정한 내부 transport 지표로부터 계산한 **잠정(provisional) net**이다. 잠정 net은 **모든 Reclaim commit이 반영된 최종 맵 상태**에서만 계산한다(Reclaim loop 내부의 중간 iteration 스냅샷으로 gate 하지 않는다). **rerun을 한 번 돌린 뒤**에야 알 수 있는 net으로 진입 여부를 판단하면 안 된다. 아래 “rerun 완료 후 검증” 블록의 `net > 0`은 **rerun 이후 metric 재계산** 결과다.

**`net_internal_transport_saved_after_reclaim` 기준선(정본)**: **Reclaim loop 진입 직전 스냅샷**의 내부 transport 지표를 `baseline_internal_transport_at_reclaim_entry`로 저장한다. Reclaim commit 및 (있을 경우) rerun 후 metric과 비교해 net 절약을 계산한다. 최초 Pass3 단독 시점과 혼동하지 않도록 스냅샷 phase를 trace에 기록한다.

**§12.2 budget과 동일 집계(정본)**: `net_internal_transport_saved_after_reclaim`(진입·rerun 후 모두)의 “내부 transport 칸 수” **집계 함수·소행성 내부 정의**는 §12.2의 `pass3_internal_transport_saved`·`incremental_internal_transport_added`와 **동일**해야 한다. §12.2 **스냅샷 정렬**절에 따라 `pass3_internal_transport_saved`를 Reclaim 직전에 재동기화했다면, `baseline_internal_transport_at_reclaim_entry`는 그 **직후** 측정값과 일관되게 둔다.

rerun 이후에도 다음이 유지되어야 한다.

```text
[ ] 모든 output connected
[ ] capacity safe
[ ] hard_protected corridor 유지
[ ] fixed output stub 유지
[ ] net_internal_transport_saved_after_reclaim > 0
```

rerun **완료 후 검증**은 STEP 5 Pass3와 **동일한 invariant**(연결성·capacity·hard protected·stub)를 적용한다.
route length ratio는 **rerun 직전**에 재계산한 **`baseline_route_length`(§11.4 재계산 절)** 대비 `<= baseline * 1.35`(§11)를 사용한다.
원본 Pass3 대비가 아니라, reclaim 이후 상태를 기준으로 한다. `net_internal_transport_saved_after_reclaim`은 rerun 후 metric을 **재계산**한다.

---

### 12.6 Reclaim loop 실패 처리

§12.2 budget·후보 조건을 만족하지 못하면 해당 후보만 reject한다. 의미는 §4.2와 동일하며 본 절은 요약이다.

```text
- 신규 placement가 없으면 loop 종료
- 신규 placement는 있으나 incremental routing 실패 시 해당 후보 reject
- internal transport budget 초과 시 해당 후보 reject(§12.2); iteration은 다음 후보 계속
- 여러 후보가 모두 routing 실패하면 Pass3 route만 유지하고 종료
- 기존 connected layout을 악화시키는 commit은 금지
```

---


---

## 부록: P4 체크리스트 (원문 §20)

### P4 — Reclaim Placement Loop 구현

```text
[ ] Pass3 이후 reclaimed_cells 계산
[ ] final_route_cells를 mineable 후보에서 제거
[ ] 신규 extractor + extension 후보 scan
[ ] reclaim candidate provisional commit 후 route_zone_map 재생성
[ ] gain / additional_route_cost 기준 적용(DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD, §12.2)
[ ] incremental routing 수행
[ ] reclaim_internal_transport_added 계산
[ ] internal transport spend budget 적용
[ ] capacity/connectivity 검증
[ ] 필요 시 post-reclaim Pass3 rerun 1회 수행
[ ] loop limit 적용
```
