# Epic A — 활성 구현 행 (active normalization rows)

**역할:** Epic A **구현 PR**마다 “지금 손대는 canonical trigger 행(A)”만 짧게 고정한다. 브랜치가 길어져도 **A/B 경계**를 흐리지 않게 한다.  
**정본 분류:** [epic_a_control_flow_mini_audit.md](./epic_a_control_flow_mini_audit.md) §5.3 마지막 열(PR 리뷰 A/B/Info), 게이트 §5.4.  
**스코프 상한:** [epic_a_implementation_scope.md](./epic_a_implementation_scope.md).  
**갱신:** 2026-05-12 — §5.3 스냅샷 반영; **A가 생기면** 구현 PR 오픈 시 본문 bullet을 반드시 채운다.

---

## 현재 활성 A 행 (normalization 대상)

**§5.3 PR 리뷰 기준(2026-05-12 확정): A-classified 행은 없음(0건).**

| Canonical trigger | §5.3 분류 | 비고 |
|-------------------|-----------|------|
| *(없음)* | — | 모든 행이 **B** 또는 **Info**로만 표기됨. |

**의미:** 지금 시점의 Epic A “구현”은, 팀이 [02_pipeline_recovery_control_flow.md](./02_pipeline_recovery_control_flow.md)에서 **A 경로**(정본에 맞춤)를 선택하고 mini-audit §5.3에서 해당 행을 **A로 재분류**한 뒤에야, 아래 bullet 목록이 비어 있지 않게 된다. 재분류 전에는 **코드로 §4.3 복귀를 억지로 맞추는 변경**을 하지 않는다(B·Info 고정과 충돌).

---

## 다음에 A가 되면 (운영 규칙)

1. **02**·리뷰에서 “이 trigger는 A로 간다”가 합의되면 §5.3 표에 **A**로 바꾼 커밋/PR을 먼저 둔다.  
2. **본 문서**에 canonical trigger id를 bullet로 추가한다(한 PR = 한 목록이면 충분).  
3. [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md)에는 **B만** 남기는지 확인한다(A로 빠진 행은 예외 표에서 제거·역사는 mini-audit에 남김).

---

## Forbidden (본 문서에서 구현 대상으로 삼지 않음)

- **모든 B 행** — [epic_a_mvp_exceptions.md](./epic_a_mvp_exceptions.md) 표 전부:  
  `step4_routing_failure`, `step4_capacity_failure`, `pass3_connectivity_break`, `final_validation_failure`
- **모든 Info 행** — §5.3:  
  `post_reclaim_pass3_connectivity_break`, `reclaim_incremental_failure`

---

## §5.3 전체 스냅샷 (참고·중복 방지)

| Canonical trigger | PR 리뷰 (§5.3) |
|-------------------|----------------|
| `step4_routing_failure` | **B** |
| `step4_capacity_failure` | **B** |
| `pass3_connectivity_break` | **B** |
| `post_reclaim_pass3_connectivity_break` | **Info** |
| `reclaim_incremental_failure` | **Info** |
| `final_validation_failure` | **B** |

분류가 바뀌면 **mini-audit §5.3을 먼저 고치고**, 그다음 본 문서 “현재 활성 A 행”을 맞춘다.
