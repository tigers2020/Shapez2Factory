# Replay 의미 격리 최종 검증 보고서

**역할**: Replay Isolation Verification Reviewer  
**일자**: 2026-05-13  
**정본 참조**: 요청된 `documents/canon/14_step10_replay_ui.md` · `documents/canon/03_data_schema_dto.md` 경로는 저장소에 없음. 동등 주제는 [14_step10_replay_ui.md](../Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md), [03_data_schema_dto.md](../Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md)로 확인함.

**전제(정본과 일치)**:

- Replay·NDJSON·`trace_event`는 **관측(출력)** 전용이며 런타임 입력이 아니다.
- `trace_event` 스키마는 UI·오프라인 분석 계약이며 **의미 권위(semantic authority)** 가 아니다.
- 동일 실행 내 replay 스냅샷은 **런타임 분기·상태 머신을 바꾸지 않는다**(append-only 수집 후 `finalize` 등에서 조립).

---

## 1. 런타임이 금지 소스를 읽지 않는지

### 1.1 `latest.ndjson` / `replay_latest.ndjson` / per-run `*.ndjson`

- **쓰기·트렁케이트**: [`django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_trace.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_trace.py) — `_replay_log_paths`, `_debug_log_paths`, `_truncate_replay_files` 등. 모듈 상단 docstring에 알고리즘 경로는 **디스크 NDJSON을 읽어 판단하지 말 것**이 명시됨.
- **코드 검색**: `django_apps/shapez_asteroid/services/asteroid_mining_layout/**/*.py`에서 `open(` … `ndjson`, `read_text` … `ndjson` 패턴 **미발견**. NDJSON 파일명 문자열은 `solver_trace.py`의 경로 구성·문서용 주석에 한정됨.
- **예외(의도적)**: `scripts/debug/*.py` 등 오프라인 도구가 `latest.ndjson` 등을 읽음 — [`solver_trace.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_trace.py) 주석과 동일하게 **감사·UI보내기·회귀** 용도로만 존재.

### 1.2 `replay_events` (동일 실행 리스트)

- 파이프라인 단계는 `replay_events`에 **append**만 수행 (`pass3.py`, `step4.py`, `p4_reclaim.py`, `recovery_orchestrator.py`, `finalize.py` 등).
- **정책 스캔 금지**: [`tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py`](../../tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py) `test_solver_pipeline_does_not_iterate_replay_events_for_policy` — `solver_pipeline/*.py` AST 상 `for`/`comprehension`의 `iter`가 `replay_events`인 경우 없음.
- **핵심 알고리즘 파일**: [`tests/unit/shapez_asteroid/test_step10_replay_contract.py`](../../tests/unit/shapez_asteroid/test_step10_replay_contract.py) `test_core_algorithm_files_do_not_read_replay_events_list` — `pass3_greedy_core.py`, `pass3_transport.py`, `step4_merge_routing.py`에 문자열 `replay_events` 없음.

### 1.3 `solver_summary`

- 파이프라인 내부: `summary_fields`는 단계 간 **DTO/요약**으로 채워지며, **이전 NDJSON의 solver_summary를 읽어오는 경로 없음** (`solver_service.build_solver_timeline` docstring: 출력만).
- **어댑터/UI**: [`django_apps/shapez_asteroid/views.py`](../../django_apps/shapez_asteroid/views.py) `_merge_solver_summary_ui_fields_into_last_map_summary` — **solve 완료 후** 타임라인 마지막 스텝에 UI 필드를 합성. 이는 솔버 코어 분기가 아니라 **표시 계층** 브릿지(아래 5절).

### 1.4 trace 스냅샷 / `trace_event` 페이로드

- `trace_event` / `debug_trace_event` 호출은 **기록** 목적 (`solver_trace`, `pass2_spine`, `pass3`, `step4`, `p4_reclaim` 등).
- reclaim 쪽 docstring([`reclaim_corridors.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/reclaim/reclaim_corridors.py))은 replay·trace를 **권위 소스로 쓰지 말 것**을 반복 명시.
- **역주의**: `step4_p2c_corrective.py`가 `solver_replay_events.normalize_replay_transport_kind`를 호출 — 이름은 replay이나 **문자열 정규화 헬퍼**로만 쓰이며, 이벤트 리스트를 읽지는 않음(남은 위험: 이름이 “replay”라 오해 소지).

### 1.5 debug-only 필드

- `SHAPEZ_SOLVER_ALGO_DEBUG`, `SHAPEZ_SOLVER_TRACE_PLACEMENT_VERBOSE` 등은 **로깅 게이트**이지, 꺼졌을 때 다른 알고리즘 분기로 이어지는 패턴은 상기 검색·테스트 범위에서 별도 “NDJSON 읽기” 증거 없음.
- `trace_enabled()`가 False여도 **동일 입력에 대한 핵심 결정**은 스테이지 계약·맵에 의존해야 하며, 이는 회귀 테스트로 부분 보장됨(전수 정적 증명은 아님).

---

## 2. Replay 레이어 동작

- [`solver_replay_events.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py): `prepare_replay_events_for_snapshot`, `build_solver_replay_snapshot`, `existing_layout_replay_overlay` 등 — **출력 조립·스키마 보강**.
- [`finalize.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver_pipeline/finalize.py): `replay_events`를 `build_final_solver_output` 쪽으로 넘겨 **같은 실행의 스냅샷**을 구성(주석: 정책 입력 아님).

---

## 3. `computation_cycle` 스트리밍

- [`solver_replay_events.normalize_replay_events_computation_cycles`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py): 이벤트 리스트 순서대로 `1..n` 부여.
- [`prepare_replay_events_for_snapshot`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py): 위 정규화 + `enrich_replay_events_event_types`.
- **UI 틱**: [`test_step10_replay_contract.py`](../../tests/unit/shapez_asteroid/test_step10_replay_contract.py) `test_prepare_replay_events_sets_schema_and_stream_tick_at_cycle_10` — 10번째 이벤트에 `computation_cycle == 10`, `visualization_stream_tick is True` (§16.1과 정합).

---

## 4. Replay 스냅샷 생성 결정론

- `computation_cycle` 부여는 **리스트 순서 고정 시 단조 증가**로 결정론적.
- `prepare_replay_events_for_snapshot`는 입력 `events` 리스트를 제자리 갱신; 동일 입력·동일 코드 버전이면 동일 출력(단, 딕셔너리 키 삽입 순서는 이벤트 소스 순서에 종속).

---

## 5. UI replay 지원 범위

| 요구(§16) | 근거 |
|-----------|------|
| Pass 스냅샷 | `build_solver_timeline` → `solver_replay`에 `layout_snapshot_before_pass3` / `after` 등 ([`test_build_solver_timeline_replay_has_step10_root_fields`](../../tests/unit/shapez_asteroid/test_step10_replay_contract.py)). |
| Pass3 before/after 오버레이 | `PASS3_LAYOUT_SNAPSHOT` 이벤트 + `build_solver_replay_snapshot` ([`test_build_solver_replay_snapshot_pass3_snapshot_refs_and_overlay`](../../tests/unit/shapez_asteroid/test_step10_replay_contract.py)). |
| recovery 시각화 | `RECOVERY_BRANCH` 등 이벤트 kind, `recovery_trigger` trace 키, `placement_recovery_overlay` 루트 필드. |
| reclaim 시각화 | P4 단계 replay append + 회귀(예: [`test_corridor_delta_replay.py`](../../tests/unit/shapez_asteroid/test_corridor_delta_replay.py), [`test_solver_replay_frames.py`](../../tests/unit/shapez_asteroid/test_solver_replay_frames.py) 등). |

---

## 6. 남은 위험

1. **정적 검사 한계**: `replay_events`를 속성 체인(`ctx["replay_events"]`)으로 순회하는 패턴은 본 보고서의 AST `Name` 검사로는 완전히 배제되지 않음 — 현재 `grep`/`ast` 샘플에서는 미발견.
2. **미래 회귀**: 새 스테이지 파일이 `replay_events`를 읽어 `if` 분기하면 테스트가 깨져야 하나, 파일이 `solver_pipeline` 밖(예: `placement/` 깊은 곳)이면 `test_solver_pipeline_*`만으로는 미커버 가능.
3. **이름 공유**: `normalize_replay_transport_kind`처럼 replay 네임스페이스를 **순수 함수**로 빌렸을 때, “replay 읽기”로 오인될 수 있음 — 문서·리네임으로 명확화 여지.
4. **뷰 계층**: `views.py`가 `solver_out["solver_summary"]`를 읽는 것은 **API 응답 조립**이므로 격리 위반이 아니나, “UI가 summary를 다시 솔버에 넣지 않는지”는 별도 API 계약으로 관리해야 함(현 검토 범위: mining layout solver 파이프라인 내부).

---

## 7. 남은 호환·브릿지

- **`solver_summary` → 타임라인 요약 병합** (`views.py`): 옵티마이저 UI 편의. 코어와의 경계는 “solve 이후”가 전제.
- **오프라인 스크립트** (`scripts/debug/*`): NDJSON에서 `decoded`/`solver_summary` 추출 후 **새 실행** — 런타임 격리와 충돌하지 않도록 CLI 전용 유지가 필요.

---

## 8. 나중에 제거 가능한 디버그 리더(후보)

- `scripts/debug/t7_verify_step4_ndjson_telemetry.py` — `latest.ndjson` 검증용 일회성·CI 보조.
- `scripts/debug/aggregate_pass12_recoverability_from_ndjson.py`, `pass12_preserve_recovery_ab.py`의 trace NDJSON 입력 경로 — 운영 코드와 디렉터리만 분리 유지 권장(삭제는 사용자 워크플로 확인 후).

---

## 9. 신뢰도 평가

| 구간 | 신뢰도 | 이유 |
|------|--------|------|
| NDJSON 디스크 미읽기(서비스 레이아웃 패키지) | **높음** | 경로 문자열 집중도·grep 부재. |
| `replay_events` 비순회(파이프라인) | **높음** | AST 테스트 + append-only 사용처. |
| `computation_cycle` / stream tick | **높음** | 단위 테스트 직접 단언. |
| 전체 저장소 전수(플러그인·다른 앱) | **중간** | 본 검토는 `asteroid_mining_layout` 솔버 체인 중심. |

**종합**: 채굴 레이아웃 솔버 파이프라인 기준 **replay 의미 격리는 정본과 정합**하며, STEP10 계약 테스트가 핵심 고정점으로 동작함.

---

## 10. 검증(실행)

다음 명령을 실행했고 **25 passed**.

```text
python -m pytest tests/unit/shapez_asteroid/test_step10_replay_contract.py ^
  tests/unit/shapez_asteroid/test_solver_replay_frames.py ^
  tests/unit/shapez_asteroid/test_runtime_authority_leakage_regression.py::test_recovery_orchestrator_does_not_iterate_replay_events_for_policy ^
  tests/unit/shapez_asteroid/test_recovery_return_paths_algorithm.py::test_solver_pipeline_does_not_iterate_replay_events_for_policy -q
```

(PowerShell에서는 `^` 대신 `` ` `` 또는 한 줄 명령 사용.)

---

## 11. 이후 진행 제안

- `documents/canon/`에 14·03 정본을 두는 경우, 본 보고서 상단 링크를 해당 경로로 갱신.
- `placement/` 전역에 대해 `replay_events` 문자열 금지 테스트를 한 단계 확장할지(회귀 비용 vs 이득) 선택.
