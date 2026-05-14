# S0_orphan_transport_preserve_loss_audit

**역할**: Solver Architecture Auditor (읽기 전용)  
**범위**: 정본 문서 `documents/Algorithm/mining_solver_cursor_sessions/*`, 구현 `django_apps/shapez_asteroid/services/asteroid_mining_layout/`, 단위 테스트, NDJSON/replay 산출물  
**금지**: 코드·테스트·리팩터 변경 없음  

---

## 1. 실행 요약 (관측 시나리오 정합)

사용자가 제시한 패턴(유체 파이프가 `orphan_component`, `trunk_seed_candidate_count = 0`, Pass2 프로브 goal 0, `preserve_missing_stub_summary.drop_count = 10`, `no_same_kind_route` 10회, Pass3 무이득, replay 프레임 소스 불일치)은 **아래 구현 경로와 정합**된다.

- **외부에 닿지 않는 유체 파이프만** 있으면 ELA에서 `main_trunk_candidate`가 없고 `trunk_seed_cell_union`이 비어, `build_trunk_seed_candidates_by_kind`가 **margin ∪ hint** 중 hint가 공집합이 된다.
- Pass2 프로브에서 **margin·기존 외부 도달 trunk·trunk_seed·raw_goal**이 모두 비면 `final_goal_count == 0`이 된다 (`pass12_route_probe.py`).
- Preserve stub 복구는 **동일 kind 목표 셀**으로의 BFS에 의존하므로, 목표 집합이 비거나 도달 불가면 `no_same_kind_route`로 누적된다 (`pass12_preserve_stub_route_recovery.py`).

**로그 증거 한계**: 워크스페이스의 `var/asteroid_mining_layout_debug/latest.ndjson`은 짧은 `run_start`/`run_end`만 포함해 위 카운터를 인용할 수 없었다. `var/asteroid_mining_layout_replay/replay_latest.ndjson`은 **빈 파일**이었다. 아래 표·답변은 **소스 + 정본 문서** 기준이다.

---

## 2. 특정 질문별 답변 (파일·함수·라인)

### 2.1 `step4_trunk_seed_candidate_zero_reason`은 어디서 나오는가?

| 위치 | 내용 |
|------|------|
| `step4_merge_routing.py` | `trace_tl["step4_trunk_seed_candidate_zero_reason"]` ← `_tseed_cnt == 0`일 때 `diagnose_trunk_seed_pool_empty(...)` 호출 (대략 1107–1116행 근처) |
| `step4_goal_trunk_seed.py` | `diagnose_trunk_seed_pool_empty` (116–141행): `no_existing_layout_context`, `exterior_margin_empty_and_no_seed`, `no_main_component`, `main_component_wrong_kind`, `all_candidates_filtered_by_policy` 등 |
| Pass2 프로브 | `pass12_route_probe.py` 486–496행: `trunk_seed_candidate_zero_reason` ← `diagnose_trunk_seed_candidate_zero_for_kind` (kind별) |

### 2.2 `exterior_margin_cell_count`, `trunk_seed_candidate_count`, `same_kind_trunk_seed_count`, `existing_trunk_goal_count`, `raw_goal_count`, `final_goal_count`가 모두 0인 이유

`pass12_route_probe.py`의 goal trace(454–463행 부근):

- `exterior_margin_cell_count = len(margin)` — `margin`이 비면 0.
- `trunk_seed_candidate_count = len(seeds_for_kind)` — `build_trunk_seed_candidates_by_kind`가 kind별로 **margin ∪ ELA trunk_seed 힌트**만 넣음 (`step4_goal_trunk_seed.py` 172–187행). 힌트가 비고 margin도 비면 0.
- `same_kind_trunk_seed_count = len(seeds_for_kind - margin)` — 둘 다 비면 0.
- `existing_trunk_goal_count = len(existing_reaching)` — 프로브 전 **외부 도달** 같은 kind belt/pipe가 없으면 0.
- `raw_goal`은 `build_step4_goal_set` 결과; 첫 라우트 모드에서 seeds∪margin이 공집합이면 0.
- `final_goal_count = len(raw_goal | trunk_now)` — `trunk_now`도 비면 0.

즉 **“외부 margin 생성 실패 또는 빈 universe + orphan-only transport + 비어 있는 trunk_seed_cell_union”** 조합이면 일괄 0이 된다.

### 2.3 기존 orphan 유체 파이프는 어디서 분류되는가?

`existing_layout_analysis.py` `_analyze_one_transport_kind` (111–167행):

- `reaching`과의 교집합으로 `comp_reaches[i]` 계산.
- `len(c) >= 2`이고 `not touches` → **`orphan_component`** (151–152행).
- `trunk_seed` 집계는 **`st2 == "main_trunk_candidate"`** 인 컴포넌트만 (392–393행). orphan은 `cleanup`으로만 들어감 (394–395행).

### 2.4 `orphan_component`가 trunk_seed로 직접 승격되는가?

**아니오** (정본과 구현 일치).

- ELA `solver_hints.trunk_seed_cell_union`에는 `main_trunk_candidate`만 들어간다 (`existing_layout_analysis.py` 392–414행).
- `trunk_seed_union_from_existing_layout`은 **`trunk_seed_cell_union`만** 파싱하고 cleanup/artifact는 명시적으로 무시한다 (`step4_goal_trunk_seed.py` 69–76행, 모듈 docstring 3–5행).
- STEP4 컨텍스트 주석: cleanup/artifact는 trunk seed에 merge되지 않는다 (`step4_merge_routing.py` 349–351행 근처 주석).

### 2.5 `orphan_component`가 `hard_protected`로 직접 승격되는가?

**ELA에서 디코드 직후 hard로 올리지는 않는다** — reclaim은 `routing_state`만 권위로 삼고 ELA hints는 읽지 않는다 (`reclaim_corridors.py` 1–7행, 170–175행).

다만 **STEP4 commit 이후** `hard_protected_corridors`는 **각 committed route의 stub + path 마지막 셀**에서 생성된다 (`step4_routing_state.py` 108–131행). 이것은 “orphan을 hard로 승격”이 아니라 **새로 커밋된 route의 기하**이다. orphan 기존 파이프는 이 풀에 **자동 포함되지 않는다**(별도 route commit 없으면).

### 2.6 orphan-island → exterior **bootstrap route** 존재 여부

리포지토리 전역 검색(`orphan_island`, `external_bootstrap` 등)에서 **구현 참조 없음**. (git 상태에 untracked `bootstrap/orphan_island_external_bootstrap.py`가 보였으나, **본 워크스페이스 파일 트리에서는 검출되지 않음**.)  
→ **현재 추적 코드 기준: 부트스트랩 경로 없음.** 정본 §08/§11이 기대하는 “고아 섬을 외부로 연결하는 선행 bootstrap”이 빠져 있으면, 본 감사에서 본 현상이 재현 가능하다.

### 2.7 Preserve recovery Tier A/B/C/D가 `no_same_kind_route`로 전부 실패하는 이유

`pass12_preserve_stub_route_recovery.py`:

- 복구는 **same-kind** transport goal에 대한 BFS/프로브에 의존 (`try_preserve_stub_route_recovery` docstring 1362행, `goal_transport_cells` 등).
- 목표 셀이 없거나, 경로상이 모두 wrong role/blocked이면 `no_same_kind_route`로 종료되는 분기가 다수 (grep: 881, 1771–1786행 등).

**근본**: 2.2와 같이 **goal/margin/trunk_seed가 비는 선행 조건**이면 모든 tier가 동일하게 실패할 수 있다.

### 2.8 Preserve missing stub 복구가 **외부 bootstrap route보다 먼저** 시도되는가?

파이프라인 상 Pass12 merged seed / preserve 로직은 STEP4 라우팅 전 단계에서 동작한다(예: `step4_merge_routing` 진입 전 pass12 통합).  
**외부 bootstrap route 구현이 없으므로** 순서 비교는 “preserve가 먼저”로 귀결된다. bootstrap이 추가될 경우 **정본상 순서·게이트를 문서에 명시**해야 drift를 막을 수 있다.

### 2.9 STEP4 성공은 “생존 57 extractor”만으로 계산되는가?

`step4_merge_routing.py`에서 `jobs = _collect_routing_jobs(cells)` (269행 등)로 **현재 맵에서 라우팅 job을 수집**한다. preserve drop 등으로 맵에서 제거된 extractor는 job에 안 남는다.  
`step4_total_stub_count`, `step4_routed_count` 등 트레이스는 이 job/placement FSM과 연동된다 (1072–1091행 부근).  
→ **“생존(맵에 남은) stub/placement 단위”가 사실상 기준**이며, 사용자 숫자 “57”은 별도 로그 검증이 필요하나 **설계상 survivor 기반**이다.

### 2.10 `preserve_source_loss_before_step4`가 STEP4 route 성공과 분리 보고되는가?

코드베이스 grep 기준 **`preserve_source_loss_before_step4` 필드명은 검출되지 않음.**  
`finalize.py` 등에서 `preserve_missing_stub_summary`, Pass3 zero-gain reason 등은 있으나, **정본이 요구하는 명시적 분리 필드는 미구현(또는 다른 키명)** 가능성이 크다 → **drift: 관측/텔레메트리 공백.**

### 2.11 hard/soft/candidate protected corridor 승격 로직

| 등급 | 구현 근거 |
|------|-----------|
| STEP4 `routing_state` hard/soft | `step4_routing_state._routing_state_from_committed_routes`: path 전체를 soft 후보에, **stub + path[-1]을 hard**에 넣고 soft에서 hard를 뺌 (116–133행). |
| ELA trunk seed | `ela_trunk_seed_candidate_corridors`로만 직렬화, **hard에 합치지 않음** (`step4_routing_state.py` 9–12행, 151–155행). |
| Reclaim 읽기 모델 `candidate` | `protected_corridors_read_for_reclaim` → `candidate = pcs.existing_layout_hints_cells` (`reclaim_corridors.py` 209–215행). 그런데 `protected_corridors_for_reclaim`는 **`existing_layout_solver_hints`를 무시**하고 `existing_layout_hints_cells`를 항상 빈 집합으로 둠 (177–178행, 156–160행). |

### 2.12 `hard_protected` 승격에 `replacement_search_exhausted` 등 증명이 필요한가?

- **문서** `12_protected_corridor.md` §14.2.2: hard는 commit 직후 **대체 탐색 소진 등 증명**과 연계해 정의.
- **구현** `step4_routing_state.py`: **모든 committed route에 대해 stub/path 끝을 hard에 넣음** — 문서의 “증명 후에만 hard”와 **불일치**(MVP 단순화).
- `step4_merge_routing.py` 775행 부근 등에서 `replacement_search_exhausted=True`는 **별 recovery 분기**에 존재하나, 위 **기본 hard 풀 구성과 동일 개념이 아님**.

### 2.13 `candidate_corridor_count == 0`인데 hard=52, soft=37인 이유

`ProtectedCorridors.candidate`는 reclaim 경로에서 **`existing_layout_hints_cells`의 별칭**이고, 런타임 권위 선택 함수는 그 힌트를 **항상 비움** (`reclaim_corridors.py` 192–215행, 특히 209–215행과 177–178행).  
`probe_candidate_cells`도 “reclaim keeps them empty at runtime” (200–201행 주석).  
→ **hard/soft는 STEP4 committed routes에서 크고, candidate는 설계상 reclaim에서 비어 있음** → 카운터 0은 **구현 의도와 문서 §14.2.1의 ‘probe 시 candidate’ 이미지 간 tension**.

### 2.14 Pass3 zero-gain 거절 원인과 summary 충분성

- `_compute_pass3_zero_gain_reason` (`finalize.py` 332–356행): `pass3_internal_transport_saved==0`이고 skip 아닐 때 문자열 휴리스틱(`hard_protected`, `replacement`, `ratio`, `connectivity`, `budget` 등); 없으면 **`no_candidate_route_improved_internal_transport`**.
- `_pass3_zero_gain_context` (359–366행): 내부 transport 카운트·`step4_route_count` 등 **제한적**이다. greedy 거절 상세 전부를 노출하지는 않음 → **UI/NDJSON에서 원인 분해가 부족할 수 있음.**

### 2.15 Replay UI/API가 `map_timeline_frame_count=6`을 `replay_frame_count=73`과 혼동하는가?

- `finalize.py` 926–946행: `map_timeline_frame_count = len(map_timeline)` vs `replay_frame_count` / `replay_event_count`를 **명시적으로 구분**하고 `trace_frame_counter_glossary`에 설명.
- `views.py` `copy_preview` docstring (259–262행): API 문서로 **동일 수치를 비교하지 말 것**을 명시.
- **버그 가능성**: 클라이언트가 glossary를 무시하면 혼동. 서버는 이미 분리 반영.

---

## 3. Drift matrix (정본 규칙 ↔ 구현 ↔ 로그 증거 ↔ 판정)

| document_rule | implementation_location | observed_log_evidence | verdict | severity | proposed_fix_sequence |
|---------------|-------------------------|------------------------|---------|----------|------------------------|
| §08 orphan은 trunk seed 아님 | `step4_goal_trunk_seed.py` + `existing_layout_analysis.py` | (로그 미제공) orphan-only 시 seed 0과 정합 | **ALIGN** | — | 유지 |
| §08 첫 route goal = margin ∪ trunk_seed | `build_step4_goal_set`, `pass12_route_probe` | margin·seed 모두 0이면 goal 0 | **ALIGN** (조건 붕괴 시 실패) | M | margin/universe 진단을 solver_summary에 강화(텔레메트리만) |
| §14 hard는 대체 불가 **증명 후** | `step4_routing_state.py` stub/path[-1] → 항상 hard | hard 카운트 다수와 독립적 증명 부재 가능 | **DRIFT** | **H** | hard 정의를 문서와 정렬(증명 플래그·route별 metadata) 또는 문서를 MVP에 맞게 CANON 갱신 |
| §14 candidate_corridor는 probe 생명주기 | `reclaim_corridors.py` candidate 항상 빈 집합 | candidate_corridor_count=0 | **DRIFT** | M | reclaim에서 candidate를 “probe 전용 trace”와 분리 표기하거나 문서 §14.2.1 수정 |
| Preserve 손실 vs STEP4 성공 분리 보고 | (필드 미검출) | preserve drop vs step4_committed 혼동 리스크 | **GAP** | M | `preserve_source_loss_before_step4` 등 CANON 키 추가(합의 후) |
| orphan island → exterior bootstrap | **미구현**(검색 0건) | trunk_seed=0 연쇄 | **GAP** | **H** | S2: bootstrap route 설계·승인 후 구현 |
| 기존 layout은 힌트만, 재구성 mineable이 정본 | 여러 모듈 주석과 reclaim 권위 분리 | — | **ALIGN** (단 bootstrap 없으면 힌트만으로 부족) | M | S2와 연계 |
| Replay vs map_timeline 카운터 | `finalize.py` + `views.py` | UI 혼동 시 “버그처럼” 보임 | **ALIGN**/클라이언트 리스크 | L | UI에서 glossary 키 표시 강제 |

---

## 4. 우선 구현 플랜 (S1–S6, 승인·플랜 게이트 전제)

1. **S1 — 증거 재현 번들**: 문제 맵 + `solver_summary` + Pass2 `pass2_probe_last_goal_trace` + `step4_trunk_seed_candidate_zero_reason` + preserve drop 상세 1건을 한 run에 묶는 최소 재현(로그만, 알고리즘 입력 금지 원칙 유지).
2. **S2 — orphan island exterior bootstrap (설계)**: 정본 §08/§11과 충돌 없이 “고아 main 없음”일 때만 동작하는 **임시 외부 연결 trunk seed** 또는 **정책상 허용되는 cheap path와 final route 분리**를 CANON에 쓰고 구현.
3. **S3 — hard_protected 의미 정렬**: (A) 구현을 문서대로 `replacement_search_exhausted` 등과 연동해 축소하거나, (B) CANON을 “MVP hard = stub+merge anchor”로 하향해 테스트·UI 문구 일치.
4. **S4 — preserve 손실 vs STEP4 telemetry**: `preserve_source_loss_before_step4` 및 rollup을 `emit_solver_summary_once` 계약에 추가(문서 §09/§10과 교차 검증).
5. **S5 — Pass3 zero-gain 분해**: `pass3_greedy_reject_detail` 또는 동등 histogram을 summary에 노출할지 결정 후 구현.
6. **S6 — reclaim candidate 카운터 의미**: `candidate_corridor_count`를 probe trace 전용으로 이름 변경하거나, ELA hint를 “diagnostic candidate”로만 채워 **정책 입력이 아님**을 UI에 고정.

---

## 5. 참조 인덱스 (핵심 파일)

- Trunk seed / 진단: `step4_goal_trunk_seed.py`  
- STEP4 트렁크 시드 zero reason: `step4_merge_routing.py` (~1108행)  
- Pass2 goal/probe: `pass12_route_probe.py` (~430–517행)  
- ELA orphan / trunk_seed / cleanup: `existing_layout_analysis.py` (~111–167, 383–414행)  
- Protected routing_state: `step4_routing_state.py`  
- Reclaim corridor DTO: `reclaim_corridors.py`, `reclaim_corridor_contracts.py`  
- Preserve recovery: `pass12_preserve_stub_route_recovery.py`, `pass12_merged_layout_seed.py`  
- Pass3 zero-gain: `finalize.py` (`_compute_pass3_zero_gain_reason`)  
- Replay 카운터: `finalize.py`, `solver_replay_ndjson.py`, `views.py` (`copy_preview`)

---

**상태**: 읽기 전용 감사 완료. 구현 변경 없음.
