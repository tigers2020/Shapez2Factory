# Placement FSM mini-audit — `PlacementCommitState` 전이(코드 변경 전)

**성격:** 읽기 전용 감사 산출물. **라우팅 휴리스틱·recovery 제어 흐름·corridor 생명주기·replay 스키마 변경 없음.**  
**정본(참고):** [08_step4_routing.md](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) §9.6, [03_data_schema_dto.md](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) §B(요지: Pass2 직후 `PROVISIONAL_PLACED`, STEP4 성공 후 `ROUTED_CONFIRMED` 등). 일반 클론에서는 위 경로가 워크스페이스에 포함된다. `documents/Algorithm/` 트리가 sparse checkout 등으로 **없을 때만** 저장소 `master` 정본을 본다.  
**Epic A와의 관계:** [epic_a_active_rows.md](./epic_a_active_rows.md) 기준 **A = 0건**이면 **Epic A §4.3 control-flow 코드 전용 PR**만 열지 않는다([epic_a_implementation_scope.md](./epic_a_implementation_scope.md)). **Placement FSM §9.6 회귀**는 Epic A 활성 A 행과 **독립**한 타일이다. 본 감사는 **placement 기반층**만 다루며, §4.3 recovery 파이프라인을 바꾸는 작업과 **섞지 않는다**.  
**merged seed 예외:** [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md) — STEP4 전 `ROUTED_CONFIRMED` 등 예외는 본 감사 **체크 목록**에 포함한다.  
**A/B/Info 분류(구현 PR 게이트):** [placement_fsm_drift_classification.md](./placement_fsm_drift_classification.md).  
**갱신:** 2026-05-12 — 표 채움(코드 기준). 다음 구현 타일(Placement FSM normalization) 착수 전 스코프·금지 사항 고정.

---

## 감사 스코프(YAML 스케치)

```yaml
name: Placement FSM mini-audit
overview: >
  Audit current placement commit state transitions against the canonical
  PlacementCommitState FSM before code changes.

targets:
  - PROVISIONAL_PLACED
  - ROUTED_CONFIRMED
  - QUARANTINED_UNROUTED
  - ROLLED_BACK

check:
  - Where each state is created
  - Where each state transitions
  - Whether ROLLED_BACK is terminal
  - Whether QUARANTINED_UNROUTED remains before final validation
  - Whether merged existing seed or preserve path bypasses FSM
  - Whether ROUTED_CONFIRMED incorrectly skips route revalidation

forbidden:
  - No routing heuristic changes
  - No recovery control-flow changes
  - No corridor lifecycle changes
  - No replay schema changes
```

---

## 점검 항목(한국어 요약)

| 항목 | 할 일 |
|------|--------|
| 생성 지점 | 각 상태가 **최초로 세팅**되는 파일·함수·조건(merged seed·preserve·일반 scratch 등)을 표로 적는다. |
| 전이 지점 | `PROVISIONAL_PLACED` → `ROUTED_CONFIRMED` / `QUARANTINED_UNROUTED` / `ROLLED_BACK` 등 **실제 분기**가 있는 호출 스택만 본다(trace 필드만으로 추론 금지). |
| `ROLLED_BACK` 종단 | 이후 **동일 placement**에 대한 승격·재라우팅이 다시 일어나는지, 종단 의미가 문서와 맞는지. |
| `QUARANTINED_UNROUTED` vs 최종 검증 | final validation 이전에 **의도적으로** 남는 경로인지, 누수·중복 확정이 없는지. |
| merged / preserve 우회 | [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md) 경로가 FSM을 **우회**하는지, 우회가 정본·플랜에서 허용된 예외인지. |
| `ROUTED_CONFIRMED`와 재검증 | “이미 확정”으로 **route 재검증을 잘못 건너뛰는** 경로가 없는지(특히 STEP4 실패·rollback 이후). |

---

## 금지(본 mini-audit 단계)

- 라우팅 **휴리스틱**·비용 함수·탐색 정책 변경  
- **recovery** 오케스트레이터·§4.3 복귀 루프·`validation_recovery` 관련 코드 변경  
- **corridor** candidate/soft/hard·atomic replace 정책 변경  
- **replay / NDJSON / event** 스키마 변경  

위는 Epic **C**·**A**(제어 흐름)·**D** 영역이며, 본 문서 범위 밖이다.

---

## 산출물(감사 완료 시 채움)

| 상태 | 생성(파일·함수) | 전이(다음 상태·조건) | 정본 대비 drift | 비고 |
|------|----------------|---------------------|-----------------|------|
| `PROVISIONAL_PLACED` | `placement/pass12_bundle_commit.py` — `_commit_after_probe` 내 `PlacementCommitRecord(..., state=PROVISIONAL_PLACED)` (대략 L286–294). Pass1/Pass2 공통; Pass2는 probe 결과가 `"uncertain"`이어도 동일하게 provisional로 남긴다(L295–303). | → `ROUTED_CONFIRMED`: `step4/step4_merge_routing.py` `run_step4_merge_aware_routing` — (1) stub이 이미 trunk에 있고 `force_route_attempt_placement_ids`에 없으면 merge shortcut으로 즉시 승격(L258–276); (2) Dijkstra·recovery 성공 후 `replace(..., ROUTED_CONFIRMED)`(L637–641). → `QUARANTINED_UNROUTED`: 동 함수에서 routing 실패·recovery 실패 시 `_rollback_placement_cells` 후 `QUARANTINED`(L481–489). merged seed에서 온 행은 이미 `ROUTED_CONFIRMED`면 이 루프의 pass2 recovery 분기(L376–378)에 안 걸림. | §9.6 요지(Pass2 직후 provisional, STEP4 성공 후 routed)와 **일치**(Pass12 commit 경로). | `unfinalized_placement_count_from_counts`에 포함(`placement_commit.py` L64–71). |
| `ROUTED_CONFIRMED` | (1) **STEP4:** `step4_merge_routing.py` — stub∈trunk shortcut(L270–275), 정상 route 성공(L637–641). (2) **merged / preserve seed:** `pass12_merged_layout_seed.py` — `seed_pass12_scratch_from_merged_existing`에서 `routed_ok` 등으로 레코드 생성 시 기본 `ROUTED_CONFIRMED`(L969–997); stub route recovery로 새 transport가 생기면 `_placement_commit_state_for_stub_route_recovery`가 provisional일 수 있음(L979–985, L100–114). | 동일 STEP4 호출 안에서는 보통 유지. **P2-C:** `step4_p2c_corrective.py` `p2c_revalidate_and_correct`가 `ROUTED_CONFIRMED`인데 trunk 연결이 끊긴 route를 찾아 재탐색; 실패 시 해당 pid는 `ROLLED_BACK`으로 바뀌고 `routes_out`에서 제거(L241–265). | **§9.6 회귀 대상(P2→A):** merged seed가 STEP4 전에 `ROUTED_CONFIRMED`를 줄 수 있음 — [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md)·[drift 분류](./placement_fsm_drift_classification.md). **동작:** stub∈trunk 시 **Dijkstra 생략**(L258–276); 진단용으로 `force_route_attempt_placement_ids`로 강제 시도 가능(L146–147, L252–256). | P2-C가 “확정 직후” 연결을 `stub_reaches_external_trunk`로 재검증하므로, shortcut으로 올린 stub도 **후속 단계에서** 깨지면 reroll/rollback된다(`step4_p2c_corrective.py` L138–152). |
| `QUARANTINED_UNROUTED` | **오직** `step4_merge_routing.py` — `run_step4_merge_aware_routing`에서 no-route·recovery 실패 시 `replace(..., QUARANTINED_UNROUTED, rollback_reason="no_route")`(L481–489). | **비종단(내부 피크):** 같은 함수 끝에서 `quarantined` 목록을 순회하며 `ROLLED_BACK`으로 덮어쓴 뒤 리스트 비움(L682–696). 반환 시점의 `placement_commit_by_id`에는 quarantine이 남지 않는 것이 정상(유닛: `test_step4_merge_routing.py`에서 quarantine count 0 기대). | 정본이 “실패 직후 상태”만 말할 경우 **구현은 중간 상태를 짧게 둔 뒤 종단으로 정리** — 문서에 “피크/비종단”을 명시하면 정합. | `unfinalized_placement_count`에 잠깐 포함되나(L64–71), STEP4 반환 전에 제거되므로 **Pass3 게이트가 이 카운트만 본다면** 피크와의 타이밍을 호출부에서 확인할 것([05](./05_placement_fsm_merged_seed.md) 항목 2와 연계). |
| `ROLLED_BACK` | (1) `step4_merge_routing.py` — 위 quarantine → terminal 정리(L688–694). (2) `step4_p2c_corrective.py` — P2-C cascade에서 broken `ROUTED_CONFIRMED` 재탐색 실패 시 `ROLLED_BACK`, `rollback_reason="p2c_trunk_disconnect"`(L241–249). | 동일 STEP4 실행 내 재승격 경로는 코드상 없음(quarantine은 곧바로 rolled_back; P2-C rolled_back은 routes에서 제거). 이후 Pass에서 새 placement id로 다시 올 수 있음(별 생애주기). | 정본 “실패 번들 롤백”과 **일치**. | **authority 2곳:** 메인 라우터의 quarantine 마무리 + P2-C 교정기. 둘 다 STEP4 패키지 안이며 역할 분리(라우팅 실패 vs trunk 단절). “단일 authority” 리팩터 시 이 두 진입점을 한 모듈/함수로 모을지가 후속 PR 쟁점. |

### 증거 요약(우선순위 3점)

1. **`QUARANTINED_UNROUTED`:** terminal 아님. 모듈 독스트링 L5–7, 본문 주석 L682–683, L685–696이 **같은 호출에서 `ROLLED_BACK`으로 소거**함을 명시.
2. **`ROUTED_CONFIRMED` vs 재검증:** 초기 확정은 stub∈trunk shortcut으로 **탐색 생략** 가능(L258–276). 이후 **`p2c_revalidate_and_correct`**가 `ROUTED_CONFIRMED`만 골라 trunk 연결 재검증(L138–152, L644–655 호출부).
3. **`ROLLED_BACK`:** `step4_merge_routing`(quarantine 종결)과 `step4_p2c_corrective`(cascade) **두 경로**; 분산 여부는 corridor/replay 작업 전 **의도적으로 문서화**해 두었음.

---

## 구현 PR로 넘어가는 게이트(참고)

1. 위 표가 **증거 링크(파일·대략 행)**와 함께 채워진다.  
2. **Placement 타일:** [placement_fsm_drift_classification.md](./placement_fsm_drift_classification.md)의 **A 행·§9.6 회귀 범위**만 코드 변경 대상으로 삼는다 — **Epic A `A=0`과 무관**.  
3. [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md)와 충돌하면 **Algorithm 정본 수정** 또는 **코드 회귀** 중 하나로 decision을 닫는다(방치 금지).

## 참고 코드(시작점)

- `placement/placement_commit.py`  
- `placement/pass12_merged_layout_seed.py`  
- `step4/step4_merge_routing.py` 및 STEP4 진입부에서의 상태 소비
