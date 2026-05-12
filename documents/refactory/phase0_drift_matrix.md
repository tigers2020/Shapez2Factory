# Phase 0 — 문서 정본 대비 구현 drift matrix

**역할:** Refactor Lead 지시에 따른 **읽기 전용** 감사 산출물이다. **코드 수정 없음.**  
**정본:** `documents/Algorithm/mining_solver_cursor_sessions/` (02, 03, 08–11, 12–14 등) + `documents/refactory/` Epic·README.  
**생성일:** 2026-05-12 (로컬 워크스페이스 기준 `rg`/파일 열람).

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
5. **Epic D** — trace/NDJSON/summary 계층 격리(현재는 대체로 출력측이나, API 병합 경로 점검 유지)

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
| **fix direction** | `recovery_validation_outcome`를 “rollup 전용”으로 이름 변경하거나, `commit_reason` 키를 §13.5 enum으로 **normalize**하는 필드 추가(`pass3_commit_reason_raw` 등). |

---

### P0-002

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-002 |
| **epic** | B |
| **severity** | high |
| **document rule** | §13.5 / §16.3 — `recovery_trigger`는 recovery **진입** 이유; 정상 P4 진행과 혼동 금지. |
| **evidence** | `solver_pipeline/p4_reclaim.py` 115–117행: P4 진입 시 `pass3_summary["recovery_trigger_reason"] = (... or RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM)`. |
| **why drift** | 정상 reclaim 경로에서도 “trigger” 필드가 채워질 수 있어, 소비자가 recovery vs phase를 구분하기 어렵다. |
| **recommended phase** | Phase 1 (Epic B) |
| **fix direction** | 정상 진행용 `p4_phase`/`p4_entry_marker` 분리; recovery 진입 시에만 `recovery_trigger_reason` 설정. |

---

### P0-003

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-003 |
| **epic** | B |
| **severity** | medium |
| **document rule** | §13.5 — `commit_reason` 확장 시 정본·계약 동기. |
| **evidence** | `pass3/pass3_transport.py` 327행부: `COMMIT_REASON_GUARDED_ATOMIC`; `pass3_greedy_core.py` 523·532행: `"normal_gain"`, `"degraded_connected_recovery"`. |
| **why drift** | 정본 열거와 추가 문자열이 공존; UI/테스트가 “허용 enum”을 가정하면 깨질 수 있다. |
| **recommended phase** | Phase 1 (Epic B) |
| **fix direction** | §13.5에 서브타입 추가 또는 `pass3_commit_subtype`로 분리 후 상위는 narrow enum만. |

---

### P0-004

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-004 |
| **epic** | A |
| **severity** | high |
| **document rule** | `02_pipeline_control_flow.md` §4.3 표 — trigger별 복귀(특히 `pass3_connectivity_break` → STEP 6, `final_validation_failure` → STEP 9만 등). |
| **evidence** | `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/recovery_orchestrator.py` — `run_solver_timeline_pipeline`: `routing_snapshot` 고정(339행), `for va in range(max_cycles)`(350행), 루프 내 `run_pass3_stage`(377–393행) → `run_p4_reclaim_stage`(394–408행) → `build_final_solver_output`(409행~). `va > 0`일 때 `RECOVERY_BRANCH` 이벤트 `phase`: `validation_recovery`(364–374행). |
| **why drift** | 문서 표의 “복귀 스테이지”와 1:1 매핑이 되지 않을 수 있다(특히 Pass3 연결성 실패 후 Reclaim 재진입 vs 동일 스냅샷 재시도). |
| **recommended phase** | Phase 2 (Epic A) |
| **fix direction** | trigger→handler 표를 코드 상수로 인코딩하고, 표와 다르면 **정본 MVP 예외** 문서화 또는 동작 수정. |

---

### P0-005

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-005 |
| **epic** | A |
| **severity** | medium |
| **document rule** | §4.2 — `cascade_corrective` vs `MAX_TOTAL_RECOVERY_ATTEMPTS` 별도 집계. |
| **evidence** | `step4/step4_p2c_corrective.py`, `finalize.py` 등 `cascade_corrective_attempts` 필드 존재. `recovery_policy.py`에 `validation_recovery`/`total_recovery` 관련 분리 로직 존재. |
| **why drift** | 필드는 있으나 문서 표 대비 “어느 루프가 카운트를 소비하는지” 추적이 필요(추가 감사). |
| **recommended phase** | Phase 2 (Epic A) |
| **fix direction** | 카운터 소비 지점을 표와 주석으로 1:1 연결; 테스트로 상한 도달 시나리오 고정. |

---

### P0-006

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-006 |
| **epic** | C |
| **severity** | medium |
| **document rule** | `12_protected_corridor.md` §14.2.1 — candidate vs soft 승격 구분. |
| **evidence** | `step4/step4_routing_state.py` 118–121행: `soft_protected_candidate_corridors`와 `soft_protected_confirmed_corridors`에 **동일** `soft_cells` 리스트. |
| **why drift** | 생명주기 단계가 요약 DTO에서 접혀 있다. |
| **recommended phase** | Phase 3 (Epic C) |
| **fix direction** | 후보/확정 분리 채우기 또는 정본에 “STEP4 요약은 동치” 명시. |

---

### P0-007

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-007 |
| **epic** | PlacementFSM |
| **severity** | medium |
| **document rule** | `08_step4_routing.md` §9.6 — Pass2 직후 `PROVISIONAL`, STEP4 성공 시 `ROUTED_CONFIRMED`. |
| **evidence** | `placement/pass12_merged_layout_seed.py` `seed_pass12_scratch_from_merged_existing` 독스트링(791행부): merged 시 `ROUTED_CONFIRMED` 가능, “STEP4 treats them as finalized”. |
| **why drift** | 엄격 FSM 문장과 merged 예외가 공존; recovery/validation 해석에 영향. |
| **recommended phase** | Phase 3 (Placement FSM, Epic A/B와 순서 조율) |
| **fix direction** | 정본에 예외 절 추가 또는 상태를 PROVISIONAL로 통일 후 STEP4 no-op 승격. |

---

### P0-008

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-008 |
| **epic** | D |
| **severity** | low |
| **document rule** | §16 — NDJSON/replay는 trace·UI; 알고리즘 입력 아님. |
| **evidence** | `solver/solver_trace.py` — NDJSON 경로는 `open(..., "a")` **append 기록** 위주(213·319행). `rg` 기준 `django_apps/shapez_asteroid` 내 `latest.ndjson`/`open(.*ndjson` **읽기** 패턴은 solver_trace 외 미검출. |
| **why drift** | 현 시점 핵심 솔버 경로에서 “NDJSON을 읽어 라우팅” 정황은 낮음. API가 `solver_replay`를 응답에 붙이는 것은 **출력**(`views.py` GET 플래그). |
| **recommended phase** | Phase 4 (Epic D) — 지속 점검 |
| **fix direction** | 알고리즘 패키지 경계에 “read 금지” 주석·(선택) import-linter 규칙. |

---

### P0-009

| 필드 | 내용 |
|------|------|
| **finding_id** | P0-009 |
| **epic** | Other |
| **severity** | low |
| **document rule** | `14_step10_replay_ui.md` §16.2 — reclaim 등 단계 가시성. |
| **evidence** | `foundation/constants.py` `SOLVER_TIMELINE_FRAME_ORDER`: Pass3 다음이 `solver_validate`이고 P4 전용 프레임 없음(주석으로 Pass3에 흡수 설명). |
| **why drift** | replay 단계 번호와 1:1이 아닐 수 있음. |
| **recommended phase** | Phase 4 또는 UI 플랜 |
| **fix direction** | P4 프레임 추가 또는 정본에 예외 명시 (`06_replay_timeline_frames.md`). |

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
