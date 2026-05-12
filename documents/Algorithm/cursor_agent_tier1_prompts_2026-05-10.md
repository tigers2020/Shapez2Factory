# Tier 1 멀티태스크 — Trace 계약 · Cursor Agent 실행 프롬프트

본 문서는 `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_trace.py` 모듈 docstring이 가리키는 **Trace contract** 정본과, Tier 1 트랙(T1~T4)별 **에이전트 실행용 복붙 프롬프트**를 한 파일에 둔다.

---

## §Trace contract — `solver_summary` · recovery · P4 · 용량

소비자: STEP10 replay / NDJSON trace / `build_solver_timeline` 호출부(예: `views.py`).

### 1) `solver_summary` 핵심 필드 (타임라인 종료 시 1회)

| 구역 | 필드 | 의미 |
|------|------|------|
| 상관 | `run_id` | `trace_run_scope` 내 UUID 축약 |
| 결과 | `return_reason` | `ok` · `validation_*` · `exception` 등 종료 사유 |
| STEP 0.5 | `existing_layout_analysis` | `analyze_existing_layout_from_mining_map` 전체 dict (또는 파이프라인 초기화 시 `None`) |
| STEP 0.5 파생 | `existing_layout_source_kind` | Pass12 stats에서 평탄화 (ELA `source_kind` 미러) |
| STEP 0.5 파생 | `existing_layout_hint_coord_count` | `solver_hints` 좌표 쌍 개수 |
| STEP 0.5 파생 | `existing_layout_barrier_cell_count` | mineable ∩ hints → Pass2 `hard_barrier_cells` 후보 개수 |
| 용량 | `capacity_mode` | 항상 `accumulate_only` (누적 모드; 하드 실패로 쓰이지 않음) |
| 용량 | `trunk_load` | STEP4 `Step4RoutingResult.trunk_load` 복사; `mode`·`edges`·`step4_*` 카운트 |
| STEP4 | `routing_state` | 보호 회랑 풀 (`hard_protected_corridors` / `soft` / nested `protected_corridors`); stub-in-trunk 병합 시 trunk spine이 soft에 포함되도록 Step4에서 확장 |
| 검증 스냅샷 | `before_return_validate` | `extractor_count`·`protected_corridor_pool_len`·`hard_protected_count` 등 최종 직전 요약 |
| Pass3 | `pass3_*` | 스킵/커밋/게인/내부 운송 제거 등 (`pass3_transport` 프레임과 정합) |
| P4 | `p4_reclaim_*` | shadow scan·루프 종료·후보 수 등 (`reclaim_shadow_commit` / `reclaim_p4_bundle` trace) |
| post-P4 | `post_reclaim_pass3_*` | 게이트·실행 여부·델타 (recovery chain과 연동) |

### 2) Recovery (`recovery_context.py` + `solver_summary` / `solver_validate` 프레임)

| 필드 | 의미 |
|------|------|
| `recovery_context_chain` | 단계 마커 리스트 (`RECOVERY_SEGMENT_*` 문자열 append-only) |
| `recovery_trigger_reason` | 예: `RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM` |
| `recovery_terminal_reason` | `finalize_recovery_terminal_reason`가 설정; post-reclaim 성공/스킵/rollback에 따라 결정 |

### 3) P4 protected pool 입력

| 소스 | 함수·모듈 | 비고 |
|------|-----------|------|
| Step4 + trunk 폴백 | `reclaim_corridors.solver_routing_state_for_p4_reclaim` | `routing_state` 우선; 키만 있고 리스트가 빈 경우 `trunk_load`로 브리지; nested `protected_corridors`가 비어 있으면 flat 리스트와 동기화 |
| Pass3 trace | `protected_corridors_for_reclaim` | solver pool 부재 시 Pass3 블록·P3-E3 touched 폴백 |
| ELA hints | `existing_layout_solver_hints` | **soft에만** 합침 (hard 불변) |

### 4) 회귀 테스트 앵커

- `tests/unit/shapez_asteroid/test_pass1_timeline_integration.py` — `solver_summary`·`solver_validate` 필수 키
- `tests/unit/shapez_asteroid/test_reclaim_shadow.py` — protected corridor · ELA merge

---

## 공통 실행 제약

- 저장소 루트: `F:/Python_Projects/shapez2Solver` (로컬 경로는 환경에 맞게 조정)
- Python 3.12, 검증 순서: `python -m pytest tests/unit/shapez_asteroid/` → `ruff check .` → `mypy .` → `black --check .`
- 솔버 동작·도메인 규칙 변경은 승인된 플랜 범위 안에서만; 레이어 경계·비밀 하드코딩 금지 (`AGENTS.md`·`root.mdc`)

---

## T1 프롬프트 (ELA → Pass12)

**목표 한 줄**: `existing_layout_analysis`를 `integrate_pass12_placement_into_working_map`에 전달하고, Pass1/Pass2에서 저위험 힌트만 소비한다.

**읽을 파일 (예시)**:

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/pass1_timeline_integration.py`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/existing_layout_analysis.py`
- `tests/unit/shapez_asteroid/test_pass1_timeline_integration.py`

**금지**: P4 reclaim 본문·`final_validation` 불변식을 요청 없이 변경하지 말 것.

**완료 조건**: 위 테스트 파일 통과; Pass12 stats에 `existing_layout_*` 메타가 기록되는지 확인.

---

## T2 프롬프트 (Step4 → P4 pool · 검증)

**목표 한 줄**: Step4가 커밋한 경로(특히 stub-in-trunk)가 P4 보호 풀에 누락되지 않게 하고, `solver_routing_state_for_p4_reclaim` 브리지를 유지한다.

**읽을 파일 (예시)**:

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/step4_merge_routing.py`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim_corridors.py`
- `tests/unit/shapez_asteroid/test_step4_merge_routing.py`
- `tests/unit/shapez_asteroid/test_reclaim_shadow.py`

**완료 조건**: `test_reclaim_shadow.py` protected corridor · ELA merge 계열 유지; Step4·reclaim 단위 테스트 추가/갱신.

---

## T3 프롬프트 (Trace 계약)

**목표 한 줄**: 본 문서 §Trace contract 표를 `solver_service` / `recovery_context` / P4 출력과 동기화하고, 타임라인 회귀로 필수 키를 고정한다.

**읽을 파일 (예시)**:

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_service.py`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/recovery_context.py`
- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_trace.py`
- `tests/unit/shapez_asteroid/test_pass1_timeline_integration.py`

**완료 조건**: 표 갱신 + (필요 시) 타임라인 테스트에 키 존재 어설션.

---

## T4 프롬프트 (문서 · 에이전트 오케스트레이션)

**목표 한 줄**: 트랙별 프롬프트와 Trace 계약을 단일 Markdown에 유지하고 `solver_trace.py` docstring 경로와 일치시킨다.

**읽을 파일 (예시)**:

- `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_trace.py`
- 본 파일 `documents/Algorithm/cursor_agent_tier1_prompts_2026-05-10.md`

**완료 조건**: docstring의 상대 경로가 본 파일을 가리키고, T1~T4 프롬프트 블록이 복붙 가능한 상태.

---

## 이후 진행

- Trace 필드가 늘어나면 **§Trace contract 표**와 `test_build_solver_timeline_solver_summary_trace_contract_keys`를 함께 갱신한다.
- Step4 `routing_state` 스키마 변경 시 T3 표·P4 소비자 문단을 동기화한다.
