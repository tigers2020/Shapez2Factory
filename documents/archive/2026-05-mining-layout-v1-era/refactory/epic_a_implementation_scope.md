# Epic A — 구현 스코프 (implementation boundary)

**역할:** Epic A **구현 PR**에서 범위가 흔들리지 않도록, 허용·금지·정본 근거를 한곳에 고정한다.  
**선행:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md)(§4.3 vs 코드 감사·A/B/Info), [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)(§4.3 트리거별 B 표).  
**갱신:** 2026-05-12 — PR #7 이후 스코프 트래커 초안. **2026-05-12** — Algorithm 정본 우선·A/B/Info 재정의(거버넌스 정렬).

**정본 계층:** 알고리즘 의미·FSM·파이프라인 단계는 **`documents/Algorithm/mining_solver_cursor_sessions/`** 가 정본이다. `documents/refactory/`는 감사·분류·순서·체크리스트용이며 Algorithm을 덮어쓰지 않는다.

**운영(Epic A 전용):** mini-audit §5.3 기준 **A-classified 행이 0건**인 동안에는 Epic A **§4.3 control-flow 코드 변경 전용 PR**을 열지 않는다. [epic_a_active_rows.md](./epic_a_active_rows.md)에 **A 행이 합의·문서로 추가**된 뒤에만 해당 PR을 연다.  
**다른 타일(예: Placement FSM §9.6):** Epic A 활성 A 행 수와 **무관**하다 — 별도 drift·플랜·PR로 진행한다.

---

## 분류 고정 (판단 원칙)

| 상태 | 의미 |
|------|------|
| **A** | 해당 Epic/타일 구현 PR에서 **normalization·회귀** 대상으로 삼을 수 있는 행(코드·계약·테스트 변경 허용). |
| **B** | **Algorithm 정본과 구현이 충돌**하거나, 즉시 맞출지 문서를 바꿀지 **decision이 보류된 행**. “영구 면제”가 아니다. 종착은 (1) 코드가 정본으로 회귀하거나 (2) Algorithm 정본이 **명시적으로** 갱신되어 새 정본이 되는 것. [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)의 B는 **§4.3 트리거 스코프**로만 해석한다(전역 B 모델 아님). |
| **Info** | 이미 정합·관측 정리용 — 본 Epic A **해당 PR**에서 행 대상으로 삼지 않음. |

**Drift 질문:** “이건 drift인가?” → Algorithm 정본·mini-audit을 먼저 본다. **B**이면 “지금 당장 PR 범위 밖”일 수는 있으나 **방치 금지** — 이슈·표에 decision(코드 회귀 vs 정본 수정)을 남긴다.

---

## Allowed (건드리는 것)

- **Epic A 구현 PR:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.4 및 [02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md)에서 **A**로 고정된 항목만 코드 변경 대상으로 삼는다.
- **현재 PR의 A 행 목록** — [epic_a_active_rows.md](./epic_a_active_rows.md)(§5.3 스냅샷).

---

## Forbidden (Epic A §4.3 구현 PR에서 건드리지 않는 것)

아래는 **Epic A control-flow 구현 PR** 범위 밖이거나, 재분류·별 PR 없이 우발적 변경을 금지한다.

- **B-classified rows (§4.3)** — [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) 표 트리거. **재분류 전** 동작 변경은 하지 않는다(주석·계약 테스트 링크는 가능). 재분류 시 mini-audit §5.3·예외 표를 먼저 갱신한다.
- **Info rows** — `post_reclaim_pass3_connectivity_break`, `reclaim_incremental_failure` 등: 본 Epic A 구현 스코프 밖.
- **routing heuristics** — Epic A 범위 밖(별도 Epic·플랜).
- **Pass3 scoring** — 동상.
- **reclaim thresholds** — 동상.
- **corridor lifecycle** — Epic C 영역; 본 스코프에서 변경 금지.
- **replay / event schema** — Epic D·trace 계층; 본 스코프에서 변경 금지.

---

## Canonical authority (정본·감사)

| 문서 | 용도 |
|------|------|
| `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3 | Recovery 제어 흐름 알고리즘 정본 |
| `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` §9.6 | Pass1/2 placement commit·`PlacementCommitState` FSM 정본 |
| [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) **§5** | §4.3 대비 구현 감사·PR 분류(A/B/Info) 작업 표 |
| [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) | §4.3 **B-only** 트리거 표(스코프는 상단 노트 참고) |

---

## 구현 PR 체크 (요약)

- [ ] 변경 대상이 **Epic A A 행**과 직접 대응하는가?
- [ ] **§4.3 B / Info / 상기 Forbidden**을 우발적으로 수정하지 않았는가?
- [ ] 정본·mini-audit가 바뀌면 §5 **재복제**·예외 표 **Revisit** 갱신을 이슈에 남겼는가?
