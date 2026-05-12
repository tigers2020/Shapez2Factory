# 솔버 상태 변이 감사·소유권·트랜잭션 경계 (2026-05-10)

본 문서는 mining layout 솔버의 **상태 일관성** 로드맵에 대응한다. 새 휴리스틱보다 **불변량·rollback·소유권**을 우선한다.

관련 코드: `django_apps/shapez_asteroid/services/asteroid_mining_layout/`  
보호 복도 세부: [`mining_solver_cursor_sessions/12_protected_corridor.md`](mining_solver_cursor_sessions/12_protected_corridor.md)  
리플레이: [`mining_solver_cursor_sessions/14_step10_replay_ui.md`](mining_solver_cursor_sessions/14_step10_replay_ui.md)

---

## 1. P0 — 상태 변이 감사 표

열: **mining_map** 변경, **routing_state** 변경, **hard/soft protected** 변경, **권위 있는 route/트렁크 표현**, **스냅샷 publish**(rollback 기준).

| 연산(모듈·책임) | mining_map | routing_state | hard/soft protected | route 권위 | 스냅샷·rollback |
|-----------------|------------|---------------|---------------------|------------|-----------------|
| Pass12 `integrate_pass12_placement_into_working_map` | 예 (Pass1/2 배치) | 아니오 | 아니오 | — | Pass1-only 스크래치 스냅샷은 Pass2 비교용 (`pass1_timeline_integration`) |
| STEP4 `run_step4_merge_aware_routing` | 예 (stub·transport·rollback) | **예** — `Step4RoutingResult.routing_state` 조립 (`_routing_state_from_committed_routes`) | `routing_state` 내 리스트로 반영 | 커밋된 STEP4 경로·stub | 실패 시 placement 단위 rollback; 맵은 함수 반환값 |
| Pass3 `run_pass3_transport_minimization_from_maps` | 예 (transport 제거/스왑) | 아니오 (요약·trace만) | Pass3 trace / E3 후보가 P4 입력 | greedy·guarded 결과 transport 그리드 | `known_good_transport_snapshot` (greedy) — E3 실패 시 복원 |
| Pass3 E3 `pass3_e3_guarded` | 스왑 시 예 | 아니오 | 후보 터치 시 검증 | replacement 경로 선행 | ABORT 시 greedy 스냅샷 |
| P4 `run_p4_reclaim_loop_after_pass3` / `reclaim_shadow_commit` | 예 (provisional·commit·rollback) | 읽기: `solver_routing_state_for_p4_reclaim(step4)` | `protected_corridors_for_reclaim`가 STEP4+Pass3 trace·ELA 힌트에서 **읽어** `ProtectedCorridorSets` 생성 | reclaim이 transport 셀 변경 | `_mining_map_snapshot` 등 루프 내 rollback |
| P4 soft replace `reclaim_soft_replace` | COMMIT 시 예 | 아니오 | soft 교체 전 replacement 연결 검증 | atomic replace 계약 | 거부 시 맵 불변(테스트 참조) |
| `solver_service.build_solver_timeline` | 위 단계 조합; 최종 `map_final` | **요약 필드**로 STEP4 `routing_state` 복사(갱신 아님) | 카운트만 `before_return_validate` | — | 예외 시 요약 `return_reason`; 단계 해시는 P4 이후 `solver_state_hash` |

**주의**: `routing_state`를 **쓰는** 주체는 사실상 STEP4 결과 조립 한 곳이며, 이후 단계는 **읽기·병합**(`reclaim_corridors.solver_routing_state_for_p4_reclaim`) 위주다. 맵은 Pass3·P4에서 계속 변할 수 있으므로 **맵과 `solver_summary["routing_state"]`의 동기**는 “STEP4 시점 고정 스냅샷”으로 이해하는 것이 안전하다.

---

## 2. P1-A — 단일 소유(권장)

| 아티팩트 | 단일 owner / publish 지점 | 비고 |
|----------|---------------------------|------|
| `hard_protected_corridors` / `soft_protected_corridors` (STEP4 의미) | STEP4 커밋 시 `routing_state`에 기록 | P4는 `reclaim_corridors`에서 풀 선택만; **집합 재정의**는 STEP4·Pass3 trace·ELA 힌트의 합성 규칙을 따름 |
| Pass3 이후 “터치된” 복도 | Pass3 trace 필드; P4가 fallback 소스로 사용 | `reclaim_corridors` 주석 참조 |
| `mining_map` 권위(파이프라인 중) | 각 단계 **함수 반환값**을 `solver_service`가 순차 대입 | 한 단계 안에서만 다중 writer 금지 원칙 |
| 단계 요약·trace | `solver_service` + `solver_trace.debug_trace_event` | `frame_id`는 `solver_timeline_frame_ids` 상수 |

**원칙**: 동일 필드를 연속 모듈이 덮어쓰지 않는다. 필요 시 **한 곳에서 publish**.

---

## 3. Atomic mutation protocol (스켈레톤 → 매핑)

| 단계 | 의미 |
|------|------|
| PREPARE | replacement 경로 계산, geometry/connectivity 사전 검증 |
| STAGE | (선택) shadow 반영·지표 재계산 |
| COMMIT | protected 스왑·맵 확정·스냅샷 갱신 |
| ABORT | 사전 스냅샷으로 맵(및 transport 역할) 복원 |

**Pass3 E3 (guarded)**: PREPARE에서 replacement·검증 → COMMIT에서 스왑 → 실패 시 ABORT로 greedy `known_good_transport_snapshot` 복원.

**P4 soft replace (`reclaim_soft_replace`)**: PREPARE에서 replacement 연결·용량 등 검증 → COMMIT에서 기존 soft 제거 후 신규 경로 반영 → 거부 시 ABORT(맵 동일).

---

## 4. 불변량 체크리스트 (우선순위 1 요약)

- Soft replace: **replacement 검증 후** 기존 corridor 제거 (`reclaim_soft_replace`).
- Pass3 E3: `replacement_route_cells` 없으면 soft 터치 거부 (`pass3_e3_guarded`).
- STEP4 rollback: placement FSM·맵 복원은 `step4_merge_routing` 책임; `routing_state`는 커밋된 경로 기준으로 조립.

---

## 5. 복도 풀·정책 (`reclaim_corridors` / `solver_permission`)

- `protected_corridors_for_reclaim`: STEP4 `solver_routing_state` → Pass3 trace → solver pool 순 **단일 소스 선택** (주석 §12.2).
- `solver_permission.pass3_permission_snapshot` / `p4_reclaim_permission_snapshot`: Pass3·P4 실행 eligibility; **상태 변이 아님**.

---

## 6. 정규화 스냅샷 해시·리플레이 (우선순위 2)

- 구현: `solver_state_hash.py` — `mining_map` 행 정렬 + (옵션) `routing_state`의 hard/soft 키만 부분 직렬화 → SHA-256.
- `build_solver_timeline`: `step_hash_step4`, `step_hash_pass3`, `step_hash_p4`, 최종 `solver_state_hash` (P4 이후 맵 기준).
- Trace: `solver_trace.debug_trace_event(..., "phase_checkpoint", frame_id=...)` — UI는 `solver_step4_routing`, `solver_pass3_transport`, `solver_p4` 등과 상관.

**Replay**: 시각화만이 아니라 **결정론적 상태 디버거**로 쓰기 위해 단계 해시·`frame_id`를 계약으로 유지한다.

---

## 7. ExistingLayoutAnalysis (우선순위 3, 보수적)

- 현재 역할: **hint layer** — `existing_layout_analysis["solver_hints"]` (trunk seed·cleanup 후보 등).
- 소비처 예: `pass1_timeline_integration` (Pass2 hard_barrier·메타), `solver_service` → P4 `existing_layout_solver_hints`, `reclaim_corridors` (`ProtectedCorridorSets.existing_layout_hints_cells`는 soft에만 합성).
- **증분 원칙**: main trunk 상속·orphan 정책을 한 번에 전 구간에 넣지 말고, stabilization 이후 단계별로 연결한다.
- 향후: `solver_hints` 스키마를 DTO로 고정하고 STEP4 `routing_state` 시드와의 연결은 별도 작은 변경으로 진행.

---

## 8. 참조 모듈 경로

- 오케스트레이션: `solver_service.py`
- STEP4: `step4_merge_routing.py`, `placement_commit.py`, `pass12_bundle_commit.py`
- Pass3: `pass3_transport.py`, `pass3_e3_guarded.py`
- P4: `reclaim_shadow.py`, `reclaim_shadow_commit.py`, `reclaim_soft_replace.py`, `reclaim_map_ops.py`
- 복도: `reclaim_corridors.py`
- Recovery 메타: `recovery_context.py`
- ELA: `existing_layout_analysis.py`, `pass1_timeline_integration.py`
