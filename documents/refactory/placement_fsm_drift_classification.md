# Placement FSM — drift A/B/Info 분류

**역할:** [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md) 산출물에 적힌 drift·증거를 **원자 항목**으로 쪼개 **A / B / Info**를 고정한다. **A/B/Info는 구현 차단 상위 권한이 아니라** PR·리뷰용 **작업 분류 라벨**이다.  
**정본:** `documents/Algorithm/mining_solver_cursor_sessions/` — 특히 [08_step4_routing.md](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) §9.6. `refactory`는 authority가 아니다.  
**선행 감사:** [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md)(표·증거 요약).  
**A/B/Info 일반 정의:** [epic_a_implementation_scope.md](./epic_a_implementation_scope.md) §「분류 고정」 — Epic A와 Placement는 **별 타일**이므로 Placement 전용 스냅샷은 아래 표·「현재 A 행」이 단일 소스다.  
**merged seed:** [05_placement_fsm_merged_seed.md](./05_placement_fsm_merged_seed.md)와 연동한다.

**금지(본 문서 단계·Placement 구현 PR 공통):** mini-audit과 동일 — 라우팅 **휴리스틱**·**recovery** §4.3 제어 흐름·**corridor** 생명주기·**replay / event** 스키마 변경은 본 타일 범위 밖(Epic A/C/D).

**갱신:** 2026-05-12 — 초기 분류. **2026-05-12** — Epic A `A=0` 게이트와 분리·B 재정의·P2 A 승격(§9.6 회귀).

---

## PR·리뷰 체크리스트(Placement 전용)

1. [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md) 표가 **실제 코드 기준 evidence**(파일·대략 행)를 갖는가.  
2. 아래 **분류 표**가 A/B/Info로 **판정 가능한 수준**인가(보류 행이 있으면 재분류 일정·근거를 남겼는가).  
3. Epic A §4.3 control-flow·`validation_recovery`를 **우발적으로** 건드리지 않는가.  
4. Epic C **corridor lifecycle**로 범위가 새지 않는가.  
5. 구현 PR 범위가 **본 타일의 A 행·또는 명시된 §9.6 회귀 목록**과 대응하는가 — **Epic A 활성 A 행 수와 무관**.

---

## 정본 대조 상태

| 정본 조각 | 로컬 경로 | 상태 |
|-----------|-----------|------|
| §9 STEP4·§9.6 `PlacementCommitState`·처리 규칙·`quarantined_placement_ids_peak` | [08_step4_routing.md](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) | **대조 완료** — P3·P5 분류에 반영. |
| DTO 요지(placement 메타 등) | [03_data_schema_dto.md](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md) | 워크스페이스에 존재; 본 표 P1·P2는 §9.6·05와 연계로 충분. §B 세부 재분류가 필요하면 별행. |

---

## 분류 표(원자 drift)

증거의 상세 파일·행은 mini-audit 표에만 두고, 본 열 **감사 역참조**는 해당 상태 행으로만 연다.

| ID | Drift 항목(원자) | 감사 역참조 | 분류 | 근거·다음 조치 |
|----|------------------|-------------|------|----------------|
| P1 | Pass12 `try_commit_*` 경로에서 `PROVISIONAL_PLACED`만 생성·Pass2 uncertain도 provisional 유지 | [mini-audit](./placement_fsm_mini_audit.md) 표 `PROVISIONAL_PLACED` 행 | **Info** | 정본 §9.6 처리 규칙 1·L170–175([08](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md))과 감사 표 정합. |
| P2 | merged / preserve `seed_pass12_scratch_from_merged_existing`가 STEP4 전에 `ROUTED_CONFIRMED` 부여 가능 | [mini-audit](./placement_fsm_mini_audit.md) 표 `ROUTED_CONFIRMED` 행; [05](./05_placement_fsm_merged_seed.md) | **B → A(회귀 PR)** | §9.6 처리 규칙 1–2와 **충돌**(decision required). **기본 권고:** `PROVISIONAL_PLACED` 유지 → STEP4에서 **no-op route commit**으로 `ROUTED_CONFIRMED` 승격. 구현 시 본 행을 **A**로 취급한다. Algorithm 정본 문장을 바꿀 경우 §9.6에 **명시적** 예외 절을 추가한 뒤 코드와 맞춘다. |
| P3 | stub∈trunk shortcut으로 Dijkstra 생략 후 `ROUTED_CONFIRMED` 승격 | [mini-audit](./placement_fsm_mini_audit.md) 표 `ROUTED_CONFIRMED` 행·증거 요약 2 | **Info** | 정본 §9.6 및 “stub이 이미 external trunk에 포함된 경우 **no-op route commit**” 보춄([08](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) §9.6)과 동일 의미의 최적화로 읽는다. 이후 **route 재검증·P2-C**는 정본 L203–216과 동일 축. |
| P4 | P2-C `p2c_revalidate_and_correct`가 `ROUTED_CONFIRMED`에 대해 trunk 연결 재검증 | [mini-audit](./placement_fsm_mini_audit.md) 표 `ROUTED_CONFIRMED` 행 | **Info** | 재검증 누락이 아님; 잘못된 bypass 보정층. |
| P5 | `QUARANTINED_UNROUTED` 비종단(함수 내부 피크) 후 동일 호출에서 `ROLLED_BACK`으로 소거 | [mini-audit](./placement_fsm_mini_audit.md) 표 `QUARANTINED_UNROUTED` 행·증거 요약 1 | **Info** | 정본 처리 규칙 6·`quarantined_placement_ids_peak`(L278)과 정합. |
| P6 | `ROLLED_BACK` 설정 authority 이중 — `step4_merge_routing`(quarantine 종결) vs `step4_p2c_corrective`(cascade) | [mini-audit](./placement_fsm_mini_audit.md) 표 `ROLLED_BACK` 행·증거 요약 3 | **Info** | 역할 분리. **선택적 후속:** `transition_to_rolled_back` 등 단일 진입점 집결은 normalization PR에서 별도 합의. |

---

## 구현 PR 게이트(Placement 타일)

1. [placement_fsm_mini_audit.md](./placement_fsm_mini_audit.md) 게이트 1·3을 만족한다.  
2. **본 문서**의 **A로 승격된 행**(현재: P2 §9.6 정렬) 또는 명시된 §9.6 회귀 범위만 코드 변경으로 삼는다.  
3. **Epic A** [epic_a_active_rows.md](./epic_a_active_rows.md)의 A 건수는 Placement PR **게이트가 아니다**.  
4. **B** 행(일반 의미: decision 대기)은 방치하지 않고 이슈·표에 종착(코드 회귀 vs Algorithm 수정)을 남긴다.  
5. 신규 drift 행은 정본([08](../Algorithm/mining_solver_cursor_sessions/08_step4_routing.md) 등) 대조 후 A/B/Info로 닫는다.

---

## 현재 A 행 스냅샷(요약)

- **A로 고정된 행:** **P2** — merged/preserve seed의 STEP4 전 `ROUTED_CONFIRMED` 선부여 제거·§9.6 처리 규칙 1–2 정렬([05](./05_placement_fsm_merged_seed.md) 권고안과 동일).  
- **보류:** 없음.

## 참고

- Epic A와의 경계: 본 타일은 **placement 기반층**만; §4.3 recovery 오케스트레이터 변경은 Epic A 플랜·게이트를 따른다.
