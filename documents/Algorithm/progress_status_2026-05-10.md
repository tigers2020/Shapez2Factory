# Asteroid Mining Solver 진척도 (2026-05-10)

> **문서 성격**: 진척도 **스냅샷**. 설계 정본은 [`Shapez2 Asteroid Mining Solver logic.md`](Shapez2%20Asteroid%20Mining%20Solver%20logic.md) 와 [`mining_solver_cursor_sessions/`](mining_solver_cursor_sessions/)이며, 본 문서는 그 정본을 **변경하지 않는다**. 본문은 2026-05-10 “Solver Architecture Reviewer” 판정과 워크스페이스 소스(예: `django_apps/shapez_asteroid/services/asteroid_mining_layout/`)를 교차 확인한 결과다.

> **갱신(코드 동기·2026-05-10 후반)**: `reclaim_shadow.py`에 P4-B2 incremental route commit, `run_p4_reclaim_loop_after_pass3` bounded loop, §14.3 `_try_atomic_replace_soft_corridor` 및 P4 루프 연동, soft replace 누적 카운트·`solver_service`의 post-reclaim Pass3 게이트가 반영됨. 아래 §1·§4·§5·§6·§7·§8은 그에 맞게 정정한다.

> **다음 핵심 단계(정정)**: **Step4 `routing_state` hard/soft corridor 풀 실제 공급** 또는 **soft replace v1을 jobs[0] 초과·다중 routing job으로 확장**(별도 설계).

---

## 1. 판정 요약

```text
P3-E3:              완료 / 종료 가능
P4-A ~ P4-B2:       완료 (B2 = incremental route commit + rollback)
P4 bounded loop:    완료 (`run_p4_reclaim_loop_after_pass3`, max iterations)
P4 §14.3 soft:      v1 완료 (atomic replace + 루프 hook; jobs[0] only 계약 문자열)
post-reclaim Pass3: solver 경로에 게이트·rerun 슬롯 존재 (정책 한도 내)
다음: Step4 protected pool 고도화 · soft replace 다중 job · capacity/replay
```

견적은 두 층으로 본다.

| 범위 | 완료율 추정 | 판단 |
|---|---:|---|
| **P4 Reclaim loop 자체** | **약 75–85%** | shadow·B1·B2·bounded loop·§14.3 soft replace hook·누적 trace. Step4 실풀·다중 soft job·UI 스트림은 미완 |
| **현재 asteroid mining layout solver 코어** | **약 72–80%** | Pass1/2/3/Step4/P4(스캔~루프~soft repair) 연결. Step4 corridor 풀 정밀도·recovery/capacity/replay는 낮음 |
| **최종 제품형 solver + replay/UI까지 포함** | **약 55–65%** | 알고리즘 코어는 많이 왔지만 STEP 6 이후 loop/recovery/UI streaming/DB·decode 연동은 별도 완성 필요 |

정확도: **중간**. 본 판단은 워크스페이스의 `django_apps/shapez_asteroid/services/asteroid_mining_layout/` 소스를 기준으로 한다. decode 모듈, UI, DB 저장, 문서 전체 정합성은 별도 게이트로 본다.

---

## 2. 근거 / 신뢰도

| 근거 | 판단 | 신뢰도 |
|---|---|---:|
| P4 Reclaim loop 정본은 Pass3 절약분 → reclaimed cells → 신규 placement scan → incremental routing → budget 검사 → validation → post-reclaim Pass3 순서 | 현재는 scan + 단일 provisional placement까지이므로 P4는 중간 단계 | 높음 |
| Reclaim 후보는 `final_route_cells`, `hard_protected_corridors`, `soft_protected_corridors`, committed placements를 제외해야 함 | 현재 `reclaim_shadow.py`가 이 제외 로직을 구현함 | 높음 |
| protected corridor는 hard/soft/source 우선순위가 필요하고 soft corridor는 replacement 없이 해제 불가 | protected source adapter가 들어간 것은 맞는 방향 | 높음 |
| Final validation은 assertion gate이며 새 route 생성 단계가 아님 | P4-B1에서 provisional placement 후 validation/rollback만 하는 것은 범위상 적절 | 높음 |
| capacity는 1차에서 rated max overflow를 검사하지 않고 누적 합산 trace 중심 | capacity overflow를 아직 보류한 것은 정본과 일치 | 높음 |

---

## 3. 소스 파일 기준 완료 상태

### 3.1 `reclaim_shadow.py` — P4-A ~ §14.3 핵심 구현

이 파일이 P4 작업의 중심이다. 행 번호는 근사치이며 에디터에서 심볼 검색을 권장한다.

| 기능 | 위치 | 상태 |
|---|---|---|
| Protected corridor DTO | `ProtectedCorridorSets` | 완료 |
| Step4 routing_state 우선 / trunk_load fallback | `solver_routing_state_for_p4_reclaim` | 완료 |
| Reclaim protected source 선택 | `protected_corridors_for_reclaim` | 완료 |
| STEP 0.5 `solver_hints` → P4 soft 병합 | `protected_corridors_for_reclaim(..., existing_layout_solver_hints=…)` · `solver_service` 전달 | 완료 (힌트는 **soft**에만 합집합, Step4/Pass3 **hard** 우선) |
| Shadow scan 결과 DTO | `ReclaimShadowScanResult` | 완료 |
| accepted candidate deterministic 선택 | `select_best_accepted_p4_bundle` | 완료 |
| provisional placement row 생성 | `_provisional_reclaim_layout_rows` | 완료 |
| P4-B1 provisional + P4-B2 incremental route | `run_p4_reclaim_provisional_commit_after_pass3`, `_p4_b2_try_commit_incremental_route` | 완료 |
| Bounded reclaim loop | `run_p4_reclaim_loop_after_pass3` | 완료 |
| §14.3 soft corridor atomic replace | `_try_atomic_replace_soft_corridor` | v1 완료 (`jobs[0]` 계약) |
| P4 루프 내 soft hook + 누적 카운트 | 동 루프 본문 | 완료 |
| Reclaim scan core | `reclaim_shadow_scan_core_after_pass3` | 완료 |
| legacy trace-only wrapper | `run_reclaim_shadow_scan_after_pass3` | 유지됨 |

**판정**

```text
P4-A:       완료
P4-A.1/B0:  완료
P4-B1/B2:   완료
P4 loop:    완료(bounded)
P4 §14.3:   v1 완료(corridor repair vs reclaim commit 구분 trace)
```

P4-B1은 **extractor / extension / stub** provisional, P4-B2는 **incremental belt/pipe 경로** 커밋(실패 시 rollback)이다. §14.3은 **soft corridor 원자 교체**로 reclaim placement commit과 별도의 “corridor repair”이며, 요약에 `p4_soft_replace_*`(last) + `p4_soft_replace_attempt_count` / `commit_count`(누적)가 실린다.

### 3.2 `solver_service.py` — P4 연결 완료

| 기능 | 위치 | 상태 |
|---|---|---|
| P4 skip placeholder | `solver_service.py` (타임라인 분기) | 완료 |
| Step4 routing_state → P4 입력 연결 | 동 파일 | 완료 |
| `run_p4_reclaim_loop_after_pass3` (스캔·provisional·B2·soft hook) | 동 파일 | 완료 |
| P4 trace를 `pass3_summary`에 병합 | 동 파일 | 완료 |
| post-reclaim Pass3 rerun 게이트 | `_post_reclaim_pass3_gate` 등 | 완료(한도·요약 필드) |
| 최종 validation 재실행 | 동 파일 | 완료 |
| 예외 시 P4 summary `setdefault` | 동 파일 | 완료 |

**판정**

```text
Solver timeline에는 P4-A ~ P4-B2 + bounded reclaim loop + §14.3 soft replace hook이 연결됨.
```

핵심: `map_final`이 **루프 종료 시점의 `map_cur`**로 갱신된다.

```python
map_final, p4_trace = run_p4_reclaim_loop_after_pass3(...)
```

### 3.3 `step4_merge_routing.py` — routing_state 슬롯 추가, 실제 풀 공급 미완

| 기능 | 위치 | 상태 |
|---|---|---|
| `Step4RoutingResult.routing_state` 필드 | `step4_merge_routing.py` ~477–485 | 완료 |
| 정상 routing 결과에서 `routing_state=None` | ~682–689 | **풀 미공급** |
| skipped 결과에서 `routing_state=None` | ~698–721 | **풀 미공급** |
| `trunk_load`는 여전히 capacity/load summary | ~666–678 | 유지 |

**판정**

```text
P4-B0.1의 구조는 됐지만, Step4가 hard/soft protected corridor pool을
실제로 채우는 정책은 아직 미구현.
```

현재 fallback 경로(`trunk_load`/`p3e3_touched`)가 있어 동작은 한다. `routing_state["protected_corridors"]`를 실제로 채우면 Reclaim의 보호 정확도가 올라간다.

---

## 4. 단계별 개발 완료율 (Solver pipeline)

| 단계 | 상태 | 완료율 추정 | 근거 |
|---|---|---:|---|
| STEP 0 Decode | 별도 모듈 | 불명 / 별도 | mining layout 솔버 zip 범위 밖 |
| STEP 0.5 Existing layout analysis | 부분 / DTO 설계 중심 | 30–45% | 기존 layout context 정본은 있으나 핵심 구현은 제한적 |
| STEP 1 Reconstruction | 부분 구현 | 55–65% | mineable/asteroid 좌표 유틸·validation 기반 있음 |
| STEP 2 Pass1 outer placement | MVP 구현 | 60–70% | `pass1_outer_placement.py`, bundle gate. beam/topology 최적화 제한적 |
| STEP 3 Pass2 internal fill | MVP 구현 | 55–65% | `pass2_internal_placement.py`, `pass2_spine.py`. 내부 최적화는 미흡 |
| STEP 4 Merge-aware routing | 중상 | 65–75% | Dijkstra route, FSM, rollback/quarantine. capacity overflow/hard-soft pool 미완 |
| STEP 5 Pass3 | 높음 | 80–88% | P3-E3 guarded atomic commit, post validation rollback, fixture까지 완료 |
| STEP 6 Reclaim loop | 중상 | 72–82% | shadow·B1·B2·bounded loop·§14.3 soft repair·zone 누적. Step4 실풀·다중 job·정본 100% 정합은 미완 |
| STEP 7 Post-reclaim Pass3 rerun | 부분 | 35–50% | `solver_service` 게이트·rerun 한도·요약 필드 존재. 정본 대비 metric/rollback 시나리오는 제한적 |
| STEP 8 Recovery branch | 부분 / 산발 | 25–40% | rollback/recovery 일부. 정본 P5 전체는 아님 |
| STEP 9 Final validation | 중상 | 70–80% | geometry/connectivity validation. capacity hard gate 후속 |
| STEP 10 Replay/UI trace | 부분 | 35–50% | trace 필드는 다수, 실시간 cycle streaming/UI는 별도 |

---

## 5. 완료 선언 가능 항목

### 5.1 완료

```text
P3-E3 guarded atomic commit
P3-E3 post-swap validation rollback
P3-E3 would_accept=True real fixture
P4-A reclaim shadow scan
P4-A.1/B0 protected corridor source adapter
P4-B0.1 routing_state wiring
P4-B1 single provisional reclaim placement commit
P4-B2 incremental route commit + rollback
P4 bounded reclaim loop (`run_p4_reclaim_loop_after_pass3`)
P4 §14.3 soft corridor atomic replace + loop hook + attempt/commit counts
```

### 5.2 완료에 가까움

```text
STEP 4 routing core
STEP 9 final geometry/connectivity validation
Pass1/Pass2 MVP placement pipeline
```

### 5.3 미완

```text
P4: Step4에서 hard/soft corridor 풀 고정 공급(routing_state 실채움)
P4: soft replace v1 → routing job 다중·후보 다중 확장
P4: reclaim / soft repair UI 요약( last vs count 구분 표시 )
P5 recovery context 표준화
capacity rated overflow hard gate
Replay UI / streaming cycle 완성
DB / SVG / decode 연동
```

---

## 6. P4 Reclaim 세부 완료율

| P4 세부 단계 | 상태 | 완료율 |
|---|---|---:|
| P4-A shadow candidate scan | 완료 | 100% |
| P4-A budget trace | 완료 | 100% |
| P4-A hard/soft/final_route 제외 | 완료 | 100% |
| P4-A.1 protected source adapter | 완료 | 100% |
| P4-B0.1 routing_state wiring | 완료 | 100% 구조 / 40% 실제 풀 공급 |
| P4-B1 single provisional placement commit | 완료 | 100% |
| P4-B2 incremental route candidate/final commit | 완료 | 100% |
| P4-C bounded loop over scans/commits | 완료 | 100% (max iterations·내부 transport 누적) |
| P4-D post-reclaim Pass3 rerun | 부분 | 50–70% | 게이트·rerun·요약; 정본 전 시나리오 미포괄 |
| P4-E reclaim budget accumulation across commits | 부분 | 60–75% | spent/루프 trace; UI·엣지 케이스 보강 여지 |
| P4-F §14.3 soft corridor atomic replace (v1) | 완료 | 100% | `jobs[0]`·계약 문자열·last+count trace |

**P4 전체**

```text
약 75–85%
```

이유: shadow → provisional → B2 → bounded loop → post-reclaim 게이트 → §14.3 soft repair까지 연결됨.
남은 것은 **Step4 실풀**, **soft replace 다중 job**, **replay/UI에서 last vs count 표시**, 정본 대비 **STEP7 시나리오 확대** 등이다.

---

## 7. 다음 작업

### 7.1 1순위 — Step4 `routing_state` hard/soft corridor 풀 실제 공급

P4 reclaim·soft replace가 **fallback·trace**로는 동작하지만, `Step4RoutingResult.routing_state=None`인 경로가 많아 **보호 복도 정밀도**가 한계다. 정본 [`12_protected_corridor.md`](mining_solver_cursor_sessions/12_protected_corridor.md)에 맞춰 최소 정책으로 풀을 채운다.

목표 형태 예시:

```python
routing_state = {
    "protected_corridors": {
        "hard": [...],
        "soft": [...],
    }
}
```

초기 정책은 단순하게 가도 된다.

```text
fixed output stubs + external-reaching trunk route cells = soft_protected
hard_protected = fixed output stubs 또는 빈 집합으로 시작
```

다만 hard 승격은 정본상 “대체 route 없음 + trunk 불가결” 증명과 연결되므로, 처음부터 과하게 hard로 올리지 않는 것이 안전하다(정본: [`12_protected_corridor.md`](mining_solver_cursor_sessions/12_protected_corridor.md)).

### 7.2 2순위 — §14.3 soft replace v1 확장

현재 구현은 **첫 routing job(`jobs[0]`)만** 대상으로 하며, trace에 v1 계약 문자열이 실린다. **여러 outlet·여러 soft 구간**을 다루려면 job 선택·충돌 셀 집합·회귀 테스트를 단계적으로 늘린다. UI/요약에서는 `p4_soft_replace_committed`(last)와 `p4_soft_replace_commit_count`(누적)를 함께 표시해 **corridor repair**와 **`p4_reclaim_loop_successful_commits`**(placement)를 구분한다.

### 7.3 견적표

| 작업 | 난이도 | 예상 리스크 | 추천 |
|---|---:|---|---|
| Step4 protected corridor pool 공급 | 중 | hard/soft 정책 과잉 고정 위험 | **다음 작업 1순위** |
| soft replace 다중 routing job | 중상 | stub/anchor 정렬·테스트 폭발 | 풀 공급 후 |
| post-reclaim Pass3 시나리오 확대 | 중 | metric baseline·rollback | 회귀 테스트와 병행 |
| capacity overflow hard gate | 상 | STEP4/recovery/validation 전부 영향 | 후속 |
| P5 recovery 표준화 | 상 | branch control flow 복잡도 | capacity 전 또는 후 별도 |
| Replay UI streaming | 중상 | backend trace ↔ frontend sync | 알고리즘 안정화 후 |

---

## 8. 최종 결론

```text
현재 개발 완료도(정정):
- P3-E3:                100%
- P4-A ~ P4-F(v1):      reclaim 루프·B2·§14.3 soft hook까지 완료
- P4 전체:              약 75–85%
- solver core 전체:     약 72–80%
- 제품형 solver+UI 전체: 약 58–68%
```

다음 선택.

```text
Step4 protected corridor pool 실제 공급
→ soft replace 다중 job / UI 요약(last vs count)
→ post-reclaim Pass3·recovery·capacity
```

---

## 부록 — 관련 파일

- 정본 본문: [`Shapez2 Asteroid Mining Solver logic.md`](Shapez2%20Asteroid%20Mining%20Solver%20logic.md)
- 분할 세션: [`mining_solver_cursor_sessions/10_step6_reclaim_loop.md`](mining_solver_cursor_sessions/10_step6_reclaim_loop.md), [`mining_solver_cursor_sessions/12_protected_corridor.md`](mining_solver_cursor_sessions/12_protected_corridor.md)
- 구현: `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim_shadow.py`, `solver_service.py`, `step4_merge_routing.py`
- 현재 계획 슬롯: [`../ai/current_plan.md`](../ai/current_plan.md) — P4 루프·§14.3 반영 후에는 “Step4 풀 공급·soft v2” 등 후속 후보를 참조
