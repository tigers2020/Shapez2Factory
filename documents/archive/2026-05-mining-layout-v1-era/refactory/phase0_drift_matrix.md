# Phase 0 — 문서 정본 대비 구현 drift matrix

**역할:** Refactor Lead 지시에 따른 **읽기 전용** 감사 산출물이다. **코드·런타임 동작 수정 없음.**  
**정본:** `documents/Algorithm/mining_solver_cursor_sessions/` (02, 03, 08–11, 12–14 등) + `documents/refactory/` Epic·README.  
**생성·갱신:** 2026-05-12 초안 → **증거 보강 라운드** (브랜치 `audit/phase0-drift-evidence`, `rg`/파일 열람). PR #2 문서 기준선 병합 후 정렬.

---

## 산출물 필수 항목 체크 (Phase 0 완료 기준)

| 항목 | 본 문서 반영 |
|------|----------------|
| drift 위치 | Finding ID (P0-001 …) |
| 실제 파일/함수/라인 | evidence 열 |
| 어떤 문서 규칙과 충돌하는지 | document rule 열 |
| 위험도 | severity 열 |
| 어떤 Epic에서 수정할지 | epic 열 |
| 최소 수정 방향 | fix direction 열 |
| 코드 수정 없음 | 본 커밋은 **문서만** |

---

## GitHub PR (base branch)

- 기본 브랜치: **`master`**. Compare 시 base가 `main`이면 PR 생성이 실패할 수 있음 → **base = `master`** 수동 선택.
- 비교 예: `https://github.com/tigers2020/Shapez2Factory/compare/master...audit/phase0-drift-evidence`

### 권장 PR 쪼개기 (한 번에 전체 회귀 금지)

| PR | 범위 |
|----|------|
| PR 1 | Phase 0 감사·본 문서만 (또는 문서 기준선) |
| PR 2 | Epic B — semantic fields |
| PR 3 | Epic A — recovery control flow |
| PR 4 | Placement FSM 정규화 |
| PR 5 | Epic C — corridor lifecycle |
| PR 6 | Epic D — trace isolation |

---

## 산출물 필수 항목 체크 (Phase 0 완료 기준)

| 항목 | 본 문서 반영 |
|------|----------------|
| drift 위치 | 각 Finding ID (P0-001 …) |
| 실제 파일/함수/라인 | evidence 열에 경로·행 번호 |
| 어떤 문서 규칙과 충돌하는지 | document rule 열 |
| 위험도 | severity 열 |
| 어떤 Epic에서 수정할지 | epic 열 |
| 최소 수정 방향 | fix direction 열 |
| 코드 수정 없음 | 본 파일은 문서만 갱신; 구현 PR은 별도 |

---

## GitHub PR (base branch)

- 이 저장소 기본 브랜치는 **`master`**이다(`origin/master` 추적). GitHub “Compare” 기본값이 `main`이면 PR 생성이 실패할 수 있으므로, **웹에서 base를 `master`로 선택**해 수동 생성한다.
- 브랜치 비교(예): `https://github.com/tigers2020/Shapez2Factory/compare/master...refactor/solver-doc-drift-phase0`

### 권장 PR 쪼개기 (한 번에 전체 회귀 금지)

| PR | 범위 |
|----|------|
| PR 1 | Phase 0 감사·본 `phase0_drift_matrix.md`만 (또는 문서 기준선) |
| PR 2 | Epic B — semantic fields |
| PR 3 | Epic A — recovery control flow |
| PR 4 | Placement FSM 정규화 |
| PR 5 | Epic C — corridor lifecycle |
| PR 6 | Epic D — trace isolation |

각 PR: **audit → 작은 시맨틱 커밋 → 테스트 → 리뷰 → merge.**

---

## 구현 우선순위 (Epic 순서와 정렬)

1. **Epic B** — semantic fields (`recovery_trigger` / `commit_reason` / rollback·reject 분리)  
2. **Epic A** — §4.3 trigger별 복귀와 오케스트레이터 정렬  
3. **PlacementFSM** — §9.6 + merged seed 예외 (`05_placement_fsm_merged_seed.md`)  
4. **Epic C** — protected corridor lifecycle + atomic replace  
5. **Epic D** — trace/NDJSON/summary 계층 격리

---

## Findings

### P0-001

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-001 |
| **epic** | B |
| **severity** | high |
| **document rule** | `11_step8_recovery.md` §13.5 — `commit_reason`은 **성공 커밋 분류**만. `recovery_trigger`는 recovery 분기 전용. |
| **evidence** | `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/recovery_policy.py` — 함수 `synthesize_recovery_validation_outcome` (124–166행), 특히 160–164행 `out["commit_reason"] = str(summary.get("pass3_commit_reason") or "validation_ok")`. |
| **why drift** | `"validation_ok"` 및 `pass3_commit_reason` 원문은 §13.5의 좁은 `commit_reason` 집합과 불일치할 수 있다. 롤업 객체가 상위 `commit_reason` 의미를 확장한다. |
| **recommended phase** | Phase 1 (Epic B) |
| **fix direction** | 롤업 키 이름 변경 또는 §13.5 enum으로 normalize + raw 필드 분리. |

---

### P0-002

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-002 |
| **epic** | B |
| **severity** | high |
| **document rule** | §13.5 / §16.3 — `recovery_trigger`는 recovery **진입** 이유; 정상 단계 진행과 혼동 금지. |
| **evidence** | `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/p4_reclaim.py` 115–117행: P4 본 루프 진입 시 `pass3_summary["recovery_trigger_reason"] = (... or RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM)`. |
| **why drift** | 정상 reclaim 실행에서도 “trigger” 필드가 채워질 수 있음. |
| **recommended phase** | Phase 1 (Epic B) |
| **fix direction** | 정상 진행 마커와 recovery trigger 필드 분리. |

---

### P0-003

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-003 |
| **epic** | B |
| **severity** | medium |
| **document rule** | §13.5 — `commit_reason` 확장 시 정본·계약 동기. |
| **evidence** | `pass3/pass3_transport.py` ~327행 `COMMIT_REASON_GUARDED_ATOMIC`; `pass3_greedy_core.py` 523·532행 `"normal_gain"`, `"degraded_connected_recovery"`. `solver_timeline.py` 171–172행: post-reclaim Pass3 trace의 `commit_reason`을 `post_reclaim_pass3_pass3_commit_reason`으로 전달. |
| **why drift** | 정본 열거 외 문자열·별도 상수 공존. |
| **recommended phase** | Phase 1 (Epic B) |
| **fix direction** | §13.5 서브타입 문서화 또는 `pass3_commit_subtype` 분리. |

---

### P0-004

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-004 |
| **epic** | A |
| **severity** | high |
| **document rule** | `02_pipeline_control_flow.md` §4.3 — trigger별 복귀(`pass3_connectivity_break` → STEP 6 등). |
| **evidence** | `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py` `run_solver_timeline_pipeline`: `routing_snapshot = copy_mining_map_rows(step4.map_after_routing)` (339행), `for va in range(max_cycles)` (350행), 루프 내 `run_pass3_stage`(377–393행) → `run_p4_reclaim_stage`(394–408행) → `build_final_solver_output`(409행~). `va>0`일 때 `RECOVERY_BRANCH` + `phase`: `validation_recovery`(364–374행). |
| **why drift** | 문서 표의 스테이지 복귀와 “동일 STEP4 스냅샷에서 Pass3→P4 재시도”가 1:1로 대응하지 않을 수 있음(특히 `pass3_connectivity_break` vs STEP 6). |
| **recommended phase** | Phase 2 (Epic A) |
| **fix direction** | trigger→handler 표 코드화 또는 MVP 예외 정본 명시. |

---

### P0-005

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-005 |
| **epic** | A |
| **severity** | medium |
| **document rule** | §4.2 — cascade vs total recovery 별도 집계. |
| **evidence** | `step4/step4_p2c_corrective.py` `cascade_corrective_attempts`; `solver_pipeline/finalize.py` summary 기본값; `recovery_policy.py` validation/total 관련. |
| **why drift** | 필드 존재 ≠ 문서 표와 소비 지점 일치; 추가 추적 필요. |
| **recommended phase** | Phase 2 (Epic A) |
| **fix direction** | 카운터 소비 지점 표·테스트 고정. |

---

### P0-006

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-006 |
| **epic** | C |
| **severity** | medium |
| **document rule** | `12_protected_corridor.md` §14.2.1 — candidate vs soft. |
| **evidence** | `step4/step4_routing_state.py` 118–121행: `soft_protected_candidate_corridors` / `soft_protected_confirmed_corridors` 동일 `soft_cells`. |
| **why drift** | 생명주기 단계 축약. |
| **recommended phase** | Phase 3 (Epic C) |
| **fix direction** | 후보/확정 분리 또는 정본 “동치” 명시. |

---

### P0-007

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-007 |
| **epic** | PlacementFSM |
| **severity** | medium |
| **document rule** | `08_step4_routing.md` §9.6 — Pass2 직후 PROVISIONAL 등. |
| **evidence** | `placement/pass12_merged_layout_seed.py` `seed_pass12_scratch_from_merged_existing` 독스트링(~791행): merged 시 `ROUTED_CONFIRMED` 가능. |
| **why drift** | 엄격 FSM 문장과 merged 예외 공존. |
| **recommended phase** | Phase 3 (Placement FSM) |
| **fix direction** | 정본 예외 절 또는 PROVISIONAL 통일 후 STEP4 승격. |

---

### P0-008

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-008 |
| **epic** | D |
| **severity** | low |
| **document rule** | §16 — NDJSON·trace는 출력·관측. |
| **evidence** | `solver/solver_trace.py` NDJSON `open(..., "a")` append(213·319행). `django_apps/shapez_asteroid`에서 `latest.ndjson` **읽기** 패턴 `rg` 미검출(알고리즘 모듈 기준). |
| **why drift** | 현 시점 라우팅 입력으로 NDJSON 읽기 정황 낮음. |
| **recommended phase** | Phase 4 (Epic D) |
| **fix direction** | 경계 주석·정적 가드 유지. |

---

### P0-009

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-009 |
| **epic** | Other |
| **severity** | low |
| **document rule** | `14_step10_replay_ui.md` §16.2 — 단계 가시성. |
| **evidence** | `foundation/constants.py` `SOLVER_TIMELINE_FRAME_ORDER`: P4 전용 프레임 없음. |
| **why drift** | replay 단계 번호와 1:1 아님. |
| **recommended phase** | Phase 4 또는 UI |
| **fix direction** | P4 프레임 또는 정본 예외. |

---

### P0-010

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-010 |
| **epic** | B / D |
| **severity** | low |
| **document rule** | `14_step10_replay_ui.md` §16.3 초안 — `event_type` 등. |
| **evidence** | 런타임 replay 이벤트는 `kind` 키(예: `recovery_orchestrator.py` 366행 `SolverMutationEventKind.RECOVERY_BRANCH`). `solver_trace.py` 269·309행 `kind`: `action`/`trace`. |
| **why drift** | 스키마 문서 `event_type` vs 구현 `kind` 명칭 불일치. |
| **recommended phase** | Phase 1 또는 4 |
| **fix direction** | 정본에 “구현 키는 `kind`” 명시 또는 export 시 미러 필드. |

---

### P0-011 (정합 — drift 아님, 오탐 방지용)

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-011 |
| **epic** | A |
| **severity** | info |
| **document rule** | `02_pipeline_control_flow.md` §4.3.2 — `post_reclaim_pass3_connectivity_break`: rerun 변경 rollback → **STEP 9**, 추가 rerun 없음. **STEP 6 재진입 아님.** |
| **evidence** | `solver/solver_timeline.py` `_run_post_reclaim_pass3_once` 165–183행: `validate_final_mining_layout(map_try)` 실패 시 **`mining_map` 원본 반환**, `post_reclaim_pass3_pass3_reverted=True`, `post_reclaim_pass3_skip_reason=final_validation_failed_after_post_reclaim_pass3`. Reclaim 루프로 되돌아가는 호출 없음. `p4_reclaim.py` 214–235행: post-reclaim Pass3 후 `tag_post_reclaim_pass3_connectivity_break`만 호출. |
| **why drift** | (해당 없음) 문서와 **충돌하지 않는** 증거로 기록. |
| **recommended phase** | — |
| **fix direction** | 유지; Epic A 수정 시 본 경로는 “정합 앵커”로 참조. |

---

### P0-012 (부분 정합 — replay_events)

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-012 |
| **epic** | D |
| **severity** | low |
| **document rule** | §16 — replay는 출력; **라우팅 분기 입력**이 아님. |
| **evidence** | `pass3.py`, `p4_reclaim.py`, `pass12_bundle_commit.py` 등: `replay_events`는 **`append`**로 이벤트 누적. 동일 패키지 내에서 **과거 이벤트를 읽어 goal/route를 바꾸는** 패턴은 본 라운드 `rg`에서 핵심 경로 미확인(리스트를 다음 단계에 **전달**만). |
| **why drift** | “누적 리스트가 커지면서 실수로 읽기” 리스크는 회귀 시 계속 점검. |
| **recommended phase** | Phase 4 |
| **fix direction** | 모듈 경계 주석·리뷰 체크리스트. |

---

### P0-013 (요약·검증 게이트 — solver_summary)

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-013 |
| **epic** | D |
| **severity** | low |
| **document rule** | §16 / Epic D — `solver_summary`는 보고·API payload; **NDJSON에서 역주입** 금지. |
| **evidence** | `finalize.py` 739행 근처 `solver_summary`: `summary_fields` 조립 출력. `recovery_policy.py` `validation_recovery_allowed(pipeline_out)`은 **`final_validation` dict** 등 **같은 실행의 파이프라인 결과**를 읽음(외부 파일 아님). `solver_trace.emit_solver_summary_once`는 trace 기록. |
| **why drift** | “summary 기반 게이트”가 trace와 혼동되기 쉬움 — 현재는 **동일 run 산출물** 기반이라 §16 “역주입”과는 구별됨. |
| **recommended phase** | Phase 4 |
| **fix direction** | 필드 출처(계산 vs 파일) 문서화. |

---

### P0-010

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-010 |
| **epic** | B / D |
| **severity** | low |
| **document rule** | `14_step10_replay_ui.md` §16.3 초안 — trace event에 `event_type` 등 스키마 필드 명시. |
| **evidence** | 런타임 replay 이벤트는 `kind` 키를 씀(예: `solver_pipeline/recovery_orchestrator.py` 366행 `"kind": SolverMutationEventKind.RECOVERY_BRANCH.value`). `solver_trace.py` 269·309행 등 `kind`: `action` / `trace`. §16.3 YAML의 `event_type` 명칭과 **필드명 불일치**. |
| **why drift** | 문서·소비자가 `event_type`만 보면 코드의 `kind`를 놓칠 수 있다. 의미 혼동은 낮으나 스키마 정렬 시 정리 대상. |
| **recommended phase** | Phase 1 (Epic B) 또는 Phase 4 (Epic D) — 계약 문서 한 줄로 동치 명시 또는 필드 별칭. |
| **fix direction** | §16.3에 “구현 키는 `kind`”를 명시하거나, export 시 `event_type` 미러 필드 추가(중복 허용 여부 합의). |

---

## 검증 범위 (본 Phase에서 수행한 것)

- `rg` 패턴: `recovery_trigger`, `commit_reason`, `recovery_trigger_reason`, `run_solver_timeline_pipeline`, `cascade_corrective`, `validation_recovery`, `latest.ndjson`, `open(` in `solver_trace.py`, replay 이벤트 `kind`.
- **테스트 미실행** (지시: 광범위 suite 불필요).

---

## 다음 액션 (코드 변경 없음)

- 본 파일을 기준으로 **PR 2 = Epic B** 범위를 쪼갠다. (PR 1은 감사·문서만 권장.)
- **하지 말 것:** Pass3 weight·Dijkstra cost·recovery 휴리스틱·replay UI·trunk_load 알고리즘·NDJSON 포맷 확장·대형 helper 통합·신규 추상화 — 현 단계는 **state semantics / control flow drift** 정리가 우선.
