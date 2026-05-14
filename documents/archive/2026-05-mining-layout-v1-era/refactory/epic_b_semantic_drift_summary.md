# Epic B — semantic drift 요약 (Part 1)

**범위:** `recovery_validation_outcome` 롤업, P4 정상 진입 마커, `finalize_recovery_terminal_reason` 게이트. 라우팅·Pass3 점수·reclaim 임계·경로 가중치는 변경 없음.

## 변경 전 → 후

| 주제 | 이전 | 이후 |
|------|------|------|
| P4 정상 진입 | `pass3_summary["recovery_trigger_reason"]`에 `post_pass3_p4_reclaim_entry` 기록 (bounded trigger와 혼동) | `p4_orchestration_entry_segment`에 동일 문자열(`P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE`). `recovery_trigger_reason`은 bounded recovery 전용(레거시 NDJSON은 `finalize` 게이트에서 `or`로 읽기 호환). |
| 실패 롤업 `commit_reason` | `return_reason != ok`여도 `pass3_commit_reason`이 있으면 롤업에 복사될 수 있음 | 실패 경로에서는 항상 `commit_reason` = `null`. |
| 성공 롤업 `commit_reason` | `"validation_ok"` 등 비정본 문자열 허용 | §13.5 취지의 허용 집합(`normal_gain`, `guarded_atomic_candidate`, `degraded_connected_recovery`)만 그대로 전달. 그 외·빈·`validation_ok`는 `normal_gain`으로 정규화. |

## 상수

- `foundation/constants.py`: `P4_ORCHESTRATION_ENTRY_SEGMENT_VALUE` (= 기존 `RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM` 문자열).

## 타임라인

- `solver_validate` 프레임 `summary`에 `p4_orchestration_entry_segment` 필드 추가.

## 회귀 테스트

- `test_recovery_contract.py`: 롤업·finalize P4 마커 분리.
- `test_pass3_transport.py`, `test_mining_solver_stabilization.py`, `test_pass1_timeline_integration.py`: 계약 키·요약 정합.

---

# Epic B — Part 2 (`event_type` vs `kind`)

**범위:** `solver_replay`의 `events[]`에만 적용. `SOLVER_REPLAY_CONTRACT_VERSION = 9`. 이벤트 생산부(STEP4/Pass3/P4 등)의 `kind` 문자열은 **변경 없음**; 스냅샷/UI 프레임 빌드 직전에 `event_type`을 파생해 채움.

## 매핑(요약)

| legacy `kind` | canonical `event_type` |
|---------------|------------------------|
| `recovery_branch` | `recovery_entered` |
| `rollback` | `transaction_rollback` |
| `step4_route_commit` | `route_added` |
| `pass12_bundle_commit` | `placement_bundle_commit` |
| `pass3_layout_snapshot` | `layout_snapshot` |
| (기타) | `REPLAY_EVENT_TYPE_BY_KIND` 참조 |

## 소비자

- `build_replay_ui_frames`: Pass3 스냅·오버레이 인덱스는 `kind` **또는** `event_type`으로 매칭(레거시 전용 이벤트·순방향 호환).

## 테스트

- `test_solver_replay_frames.py`: `test_contract_*` — 매핑 완전성, 스냅샷 enrich, `event_type` 단독 이벤트.
