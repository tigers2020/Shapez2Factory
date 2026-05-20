# Epic A — 구현 스코프 (implementation boundary)

**역할:** Epic A **구현 PR**에서 범위가 흔들리지 않도록, 허용·금지·정본 근거를 한곳에 고정한다.  
**선행:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md)(§4.3 vs 코드 감사·A/B/Info), [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)(B-only 고정 표).  
**갱신:** 2026-05-12 — PR #7(MVP 예외 문서화) 이후 스코프 트래커 초안.

**운영:** §5.3 기준 **A-classified 행이 0건**인 동안에는 Epic A **코드 변경 전용 PR**을 열지 않는다(제어 흐름 **문서·거버넌스** 단계만 유지). [epic_a_active_rows.md](./epic_a_active_rows.md)에 **A 행이 합의·문서로 추가**된 뒤에만 구현 PR을 연다.

---

## 분류 고정 (판단 원칙)

| 상태 | 의미 |
|------|------|
| **A** | 구현 **normalization** 대상(코드·계약·테스트 변경 허용 범위) |
| **B** | **의도적 MVP behavior** — [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)에 있는 행만. “canonical과 다르다 = 즉시 수정”이 **아님**. |
| **Info** | 이미 정합·관측 정리용 — 본 Epic A 구현에서 **행 대상으로 삼지 않음**. |

**Drift 질문:** “이건 drift인가?” → 먼저 mini-audit §5·예외 표를 본다. **B에 있으면** “MVP exception으로 고정”이 정답 축이다.

---

## Allowed (건드리는 것)

- **A-classified rows only** — [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.4 및 관련 플랜([02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md))에서 **A**로 고정된 항목만 코드 변경 대상으로 삼는다.
- **현재 PR의 A 행 목록** — [epic_a_active_rows.md](./epic_a_active_rows.md)(§5.3 스냅샷; A가 0건이면 코드로 정본 복귀를 억지 맞추지 않음).

---

## Forbidden (건드리지 않는 것)

- **B-classified rows** — [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) 표에 있는 트리거·경로. 필요 시 주석·계약 테스트로 **링크만** 하고 동작 변경 금지(재분류는 별도 리뷰·문서 갱신).
- **Info rows** — 예외 문서 상단과 동일: `post_reclaim_pass3_connectivity_break`, `reclaim_incremental_failure` 등 **Info** 분류는 본 Epic A 구현 스코프 밖.
- **routing heuristics** — Epic A 범위 밖(별도 Epic·플랜).
- **Pass3 scoring** — 동상.
- **reclaim thresholds** — 동상.
- **corridor lifecycle** — Epic C 영역; 본 스코프에서 변경 금지.
- **replay / event schema** — Epic D·trace 계층; 본 스코프에서 변경 금지.

---

## Canonical authority (정본·감사)

| 문서 | 용도 |
|------|------|
| [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) **§5** | §4.3 정본 표·Expected·PR 분류(A/B/Info)의 **감사 정본** |
| [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) | **B-only** single source of truth |
| `documents/Algorithm/mining_solver_cursor_sessions/02_pipeline_control_flow.md` §4.3 | 알고리즘 정본(원문은 mini-audit §5.1 링크 기준) |

---

## 구현 PR 체크 (요약)

- [ ] 변경 대상이 **A** 행과 직접 대응하는가?
- [ ] **B / Info / 상기 Forbidden** 목록을 우발적으로 수정하지 않았는가?
- [ ] 정본·mini-audit가 바뀌면 §5 **재복제**·예외 표 **Revisit** 갱신을 이슈에 남겼는가?
