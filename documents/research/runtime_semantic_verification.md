# Runtime semantic verification

**역할**: Runtime Semantic Verification Engineer  
**일자**: 2026-05-13  
**원칙**: 로그는 **증거 보조**일 뿐이며, 알고리즘 계약은 **정본·코드·회귀 테스트**로만 판정한다. NDJSON 한 줄만으로 “런타임이 이렇게 분기했다”는 식의 추론은 하지 않는다.

---

## 정본 경로 정합 (canonical mismatches)

| 사용자 요청 경로 | 저장소 |
|------------------|--------|
| `documents/canon/08_step4_routing.md` | **미수록** — 실제 정본: `documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md` [정본 §] |
| `documents/canon/11_step8_recovery.md` | **미수록** — 실제: `.../11_step8_recovery.md` [정본 §] |
| `documents/canon/14_step10_replay_ui.md` | **미수록** — 실제: `.../14_step10_replay_ui.md` [정본 §] |
| `documents/canon/02_*` (§4.3) | **미수록** — 실제: `.../02_pipeline_control_flow.md` §4.3 표 [정본 §] |

**판정**: 저장소 레이아웃과 요청 경로가 불일치한다. 구현·검증은 **Algorithm/mining_solver_cursor_sessions** 조각을 정본으로 읽었다. `documents/canon/` 신설·문서 이동은 본 작업 범위 밖.

---

## 로그 증거 (latest.ndjson)

- 워크스페이스 전역 `**/latest.ndjson` 검색 결과: **파일 없음** (미생성 또는 `.gitignore` 등으로 샌드박스에 없음).
- 따라서 본 보고서에는 **NDJSON 라인 인용 없음** [로그 발췌: 없음]. 항목 1–7은 **코드·테스트·정본**으로만 서술한다.

---

## 관측 계층: Recovery cap·Pass3 (직렬화 시맨틱)

**원칙**: 내부 런타임 비교용 센티널(`RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED == 0` 등)과, 로그·NDJSON·검증자가 읽는 **직렬화 필드**를 구분한다. 알고리즘 분기는 변경하지 않는다.

### Recovery (§13 체인 길이 vs cap)

| 필드 | 의미 |
|------|------|
| `total_recovery_attempts_used` | `recovery_context_chain` **길이 미러** (STEP4 `cascade_corrective_attempts`와 별개) |
| `recovery_context_chain_segment_count` | 위와 동일; 로그 가독용 별칭 |
| `max_total_recovery_attempts` | 레거시·호환: 무제한 모드에서 **정수 0** (내부 센티널). **“허용 0회”로 읽지 말 것** |
| `max_recovery_context_chain_segments` | 관측용: bounded일 때 양의 상한, **무제한이면 `null`** |
| `total_recovery_cap_mode` | `"bounded"` / `"unlimited"` — cap 해석 시 **이 문자열과 `max_recovery_context_chain_segments`를 우선** |

`solver_replay_contract_envelope`(`recovery_timeline_envelope`)에 `max_recovery_context_chain_segments`가 포함된다.

### Pass3 (검증 시 권위 있게 읽을 필드)

| 필드 | 검증 시 의미(요약) |
|------|-------------------|
| `pass3_map_accepted` | `validate_final` 통과 후 **최종 맵 채택** (known-good 유지 판단에 **우선**) |
| `pass3_greedy_committed` | greedy 단계 커밋 |
| `pass3_committed` | Pass3 transport 단계 **가드/유효 outcome** (`pass3_greedy_committed`와 혼동 금지) |
| `pass3_validated_layout_retained` | `pass3_map_accepted`와 동일 값(로그 가독 별칭) |
| `pass3_transport_stage_committed` | `pass3_committed`와 동일 값(로그 가독 별칭) |
| `pass3_final_committed` | 타임라인·finalize 축; **`pass3_map_accepted`와 함께** 읽기 |

`pass3_committed=False` 이고 `pass3_final_committed=True`인 조합은 **“transport 개선은 reject, 검증 통과 레이아웃 유지”**로 읽는 것이 맞다.

---

## 항목별 교차검증

### 1. Replay-derived authority 필드가 런타임 결정에 개입하지 않음

- **정본**: `14_step10_replay_ui.md` — replay/trace는 관측·UI 계약 [정본 §].
- **코드**: `solver_trace.py` 모듈 docstring — 라우팅·Pass3·Reclaim·Recovery는 디스크 NDJSON·이전 `solver_summary`·`replay_events`를 **읽어 판단하지 말 것** [코드].
- **테스트**: `test_solver_pipeline_does_not_iterate_replay_events_for_policy` — `solver_pipeline/*.py`에서 `for`/`comprehension`이 `replay_events`를 직접 순회하지 않음 [테스트]. `test_core_algorithm_files_do_not_read_replay_events_list` — `pass3_greedy_core.py`, `pass3_transport.py`, `step4_merge_routing.py`에 문자열 `replay_events` 없음 [테스트].

**판정**: 요청 범위(파이프라인·핵심 알고리즘)에서 **replay 리스트 스캔 기반 권위**는 회귀로 차단된 상태로 본다.

---

### 2. `step4_committed` 의미가 정본과 정렬됨

- **정본**: `08_step4_routing.md` §9.6 — `Step4RoutingResult`가 권위; `trunk_load["step4_committed"]`는 **복제**이며 Pass3는 `trunk_load.get(...)`로 **추론하지 않는다**; `pass3_gate_source` = `explicit_arg` [정본 §].
- **코드**: `pass3.run_pass3_stage(..., step4_committed: bool)` 인자로 게이트; `pass3_eligibility_checked` 로그 페이로드에 `step4_state_source` 고정 [코드].
- **코드**: `finalize.py` — `step4_committed`를 `step4_result.committed`에서 설정, 주석에 degraded·backward compatibility 명시 [코드].
- **테스트**: `test_runtime_authority_leakage_regression` — `trunk_load["step4_committed"]`를 Pass3/reclaim **추론**에 쓰지 않는다는 계열 [테스트].

**판정**: 정본 §9.6과 구현·회귀가 **일치**한다고 본다.

---

### 3. `committed=false` 이벤트에 `commit_reason`을 두지 않음 (요약·계약)

- **정본**: `14_step10_replay_ui.md` §16.3 — `committed=false`이면 `commit_reason` 비우고 `rejected_reason` / `rollback_reason`만 [정본 §].
- **코드**: `finalize._pass3_summary_for_solver_timeline` — `pass3_final_committed`가 False면 `pass3_commit_reason = None` [코드].
- **코드**: `pass3_f_branch_candidate` — `commit_reason = ... if committed else None` [코드].
- **테스트**: `test_pass3_timeline_summary_clears_commit_reason_when_not_final_committed` [테스트].

**판정**: 타임라인·P3F 요약 경로에서 **비커밋 시 commit_reason 제거**가 테스트로 고정됨. (NDJSON `trace_event.decision` 전 이벤트 전수는 로그 없어 미검.)

---

### 4. Recovery return paths vs §4.3

- **정본**: `02_pipeline_control_flow.md` §4.3 표 및 §4.3.1·§4.3.2 [정본 §]; `11_step8_recovery.md` 트리거별 복귀 요약 [정본 §].
- **코드**: `recovery_return_policy._POLICY_TABLE` — 트리거별 `primary_return_steps`, `reenters_step4`, `allows_extra_post_reclaim_pass3_rerun` [코드].
- **테스트**: `test_recovery_return_policy_table_matches_algorithm`, `test_d2_b2_orchestrator_step4_routing_contract_in_source`, `test_solver_pipeline_does_not_iterate_replay_events_for_policy` 등 [테스트].

**판정**: 표·코드·소스/회귀가 **동기화**되어 있다고 본다. 로그의 `recovery_trigger` 문자열만으로 복귀 경로를 **재유도**하지 않음.

---

### 5. Pass3 / reclaim / recovery 분리

- **정본**: `02` §4.1 흐름, `11` §13.5 `recovery_trigger` vs `commit_reason` 분리 [정본 §].
- **코드**: Pass3는 `run_pass3_stage`; reclaim은 `p4_reclaim`; recovery는 `recovery_orchestrator` + `validation_recovery_allowed` 등 [코드].
- **테스트**: `test_recovery_contract`, `test_recovery_return_paths_algorithm`, P4 post-reclaim 게이트 관련 테스트 [테스트].

**판정**: 레이어 분리는 **문서·모듈 경계·테스트**로 지지됨.

---

### 6. Protected corridor lifecycle (`candidate` → `soft` → `hard`)

- **정본**: `08`은 routing·placement FSM 중심; `14` 부록 P6에 hard/soft corridor **UI 레이어** 항목 [정본 §].
- **코드**: `reclaim_corridors.protected_corridors_for_reclaim` — 런타임 hard/soft는 **committed STEP4 `routing_state`**에서만; 풀이 비면 **텔레메트리 폴백 없음**; `probe_*`는 reclaim 가드에서 **비움** (“lifecycle probes belong in replay/NDJSON assembly”) [코드].
- **테스트**: `test_protected_corridors_read_matches_for_reclaim`, `test_runtime_authority_leakage_regression`의 corridor·`pass3_trace` 합성 금지 구간 [테스트].

**판정**: **런타임 reclaim 가드**에서는 `candidate`/`probe_*`가 권위 소스가 아니며, hard/soft는 `routing_state` 권한으로 고정된다. “한 줄로 candidate→soft→hard 승격” 같은 문구는 **NDJSON 조립·UI** 쪽 계약에 가깝고, 본 검증은 **코드 주석·테스트**로만 확정했다 [코드][테스트].

---

### 7. 숨은 텔레메트리 권위 누수

- **코드**: `reclaim_corridors` — `pass3_trace`만으로 hard/soft 합성 안 함 [코드].
- **테스트**: `test_runtime_authority_leakage_regression.py` 전반 (trunk_load mirror, `pass3_trace` probe, merge helper 등) [테스트].

**판정**: 알려진 누수 패턴은 **회귀로 억제**된 상태. 새 파일 추가 시 동일 테스트 패턴을 깨면 위반으로 간주 가능.

---

## Suspicious semantic drift (의심스러운 드리프트)

- **`normalize_replay_transport_kind`**가 `step4_p2c_corrective`에서 import됨 — 이름에 “replay”가 있으나 **문자열 정규화**로만 쓰일 수 있어, “replay 권위”로 오인될 여지 [코드]. 동작상 분기 입력은 아님.
- **NDJSON 미제공**: 실제 `latest.ndjson`이 없어 `trace_event.decision` 전 이벤트에 대한 **로그 단위** 검증은 수행하지 않음 [로그 발췌: 없음].

---

## Trace namespace misuse (추적 네임스페이스 오용 가능성)

- `recovery_trigger` vs `commit_reason`: 정본 `11` §13.5, `14` §16.3 — 역할 분리 [정본 §]. `recovery_policy.synthesize_recovery_validation_outcome` 등이 요약을 롤업 [코드] (본 검토: grep·테스트 이름 수준).
- `step4_state_source` 블록은 **진단용** 로그 필드로 Pass3 eligibility에 첨부됨 — **게이트 입력은 `explicit_arg`의 `step4_committed`** [코드][정본 §].

---

## Recovery branching anomalies

- **탐지 안 함**: 별도의 “분기 이상” 로그 증거 없음; `test_recovery_orchestrator_loop`, `test_recovery_return_paths_algorithm`, `test_recovery_contract` **39+ 테스트 통과**로 정상 범위만 확인 [테스트].

---

## FSM anomalies

- Placement FSM·STEP4 `committed`/`degraded`는 `08` §9.6 및 `03_data_schema_dto` 계열과 연결 [정본 §]. 본 절에서는 **회귀 통과**로 이상 없음 [테스트]. NDJSON 기반 FSM 불일치 검사는 **미실시** [로그 발췌: 없음].

---

## Confidence level

| 주제 | 신뢰도 | 근거 |
|------|--------|------|
| replay/NDJSON 비입력(핵심 경로) | **높음** | 모듈 docstring + AST/문자열 금지 테스트 [코드][테스트] |
| `step4_committed` 권위 | **높음** | §9.6 + explicit arg + 회귀 [정본 §][코드][테스트] |
| `commit_reason` 비움(타임라인) | **높음** | finalize + 단위 테스트 [코드][테스트] |
| §4.3 복귀 표 | **높음** | `_POLICY_TABLE` + 알고리즘 테스트 [코드][테스트] |
| corridor reclaim 런타임 | **중~높음** | 구현 주석 명확; UI lifecycle 문구와의 용어 정합은 문서 추가 정리 여지 [코드][정본 §] |
| NDJSON 이벤트 단위 의미 | **낮음(미검)** | `latest.ndjson` 부재 [로그 발췌: 없음] |

**종합**: 코드·정본·회귀 기준으로는 **요청 1·2·4·5·7은 강하게 지지**되고, **3은 요약 경로에서 강하게 지지**(전 trace 이벤트는 미검), **6은 reclaim 런타임 관점에서 강하게 지지**(문구상 “lifecycle” 전체는 UI/조립 측과의 용어 정합 추가 확인 여지).

---

## Validation (실행)

다음을 실행했고 **39 passed**.

```text
python -m pytest tests/unit/shapez_asteroid/test_step10_replay_contract.py tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py tests/unit/shapez_asteroid/test_runtime_authority_leakage_regression.py -q
```

`ruff`는 본 작업에서 **Python 소스 미변경**으로 생략.

---

## 이후 진행

- CI 또는 로컬에서 `latest.ndjson`을 확보한 뒤, **동일 run_id**에 한해 `trace_event`의 `decision.committed` / `commit_reason` 공존 여부만 샘플링하면 항목 3·6의 **로그 층** 신뢰도를 올릴 수 있다.
- `documents/canon/`에 08·11·14·02를 두면 요청 경로와 저장소가 일치한다.
