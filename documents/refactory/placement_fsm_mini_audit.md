# Placement FSM mini-audit — `PlacementCommitState` 전이(코드 변경 전)

**성격:** 읽기 전용 감사 산출물. **라우팅 휴리스틱·recovery 제어 흐름·corridor 생명주기·replay 스키마 변경 없음.**  
**정본(참고):** `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` §9.6, `03_data_schema_dto.md` §B(요지: Pass2 직후 `PROVISIONAL_PLACED`, STEP4 성공 후 `ROUTED_CONFIRMED` 등). 로컬 미보유 시 저장소 `master` 정본을 본다.  
**Epic A와의 관계:** [epic_a_active_rows.md](./epic_a_active_rows.md) 기준 **A = 0건**이면 Epic A **코드 전용 PR**은 열지 않는다([epic_a_implementation_scope.md](./epic_a_implementation_scope.md)). 본 감사는 **placement 기반층**만 다루며, §4.3 recovery 파이프라인을 바꾸는 작업과 **섞지 않는다**.  
**merged seed 예외:** [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md) — STEP4 전 `ROUTED_CONFIRMED` 등 예외는 본 감사 **체크 목록**에 포함한다.  
**갱신:** 2026-05-12 — 다음 구현 타일(Placement FSM normalization) 착수 전 스코프·금지 사항 고정.

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
| `PROVISIONAL_PLACED` | *(미작성)* | | | |
| `ROUTED_CONFIRMED` | | | | |
| `QUARANTINED_UNROUTED` | | | | |
| `ROLLED_BACK` | | | | |

---

## 구현 PR로 넘어가는 게이트(참고)

1. 위 표가 **증거 링크(파일·대략 행)**와 함께 채워진다.  
2. drift가 **A로 정리**된 행만 코드 변경 대상으로 삼는다(행이 없으면 문서·계약만 갱신).  
3. [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md)와 충돌하면 **문서 예외 먼저** 합의 후 코드.

## 참고 코드(시작점)

- `placement/placement_commit.py`  
- `placement/pass12_merged_layout_seed.py`  
- `step4/step4_merge_routing.py` 및 STEP4 진입부에서의 상태 소비
