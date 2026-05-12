# STEP10 리플레이 지도 오버레이 계약 (solver_replay v4)

## 목적

디코드 타임라인과 `solver_timeline` 슬라이스에 맞춰, 리플레이 이벤트·Pass3 스냅·복구 분기 등을 UI에 반영한다. 계약 버전은 **`SOLVER_REPLAY_CONTRACT_VERSION = 5`** (`route_replaced` 셀 diff·집계 포함). 이후 페이로드 확장은 v6+에서 검토.

## 데이터 정렬

- `solver_replay.ui_frames[i]`는 `solver_timeline[i]`와 **1:1** 대응한다 (`timeline_index`, `timeline_frame_id`).
- `event_indices`, `overlay_event_indices`는 **`solver_replay.events` 배열의 0 기반 인덱스**다.
- 지도 타일은 각 프레임의 `mining_map`; 요약 메타는 `summary` (프레임별로 부분 키만 있을 수 있음).

## Replay `phase` → 타임라인 프레임 (`_FRAME_ID_TO_EVENT_PHASES`)

| replay 이벤트 `phase` | 타임라인 `id` |
|------------------------|----------------|
| `pass12` | `solver_pass2_internal` |
| `step4` | `solver_step4_routing` |
| `pass3`, `p4_reclaim` | `solver_pass3_transport` |
| **`validation_recovery`** (`RECOVERY_PHASE_VALIDATION_RECOVERY`) | **`solver_validate`** |

P5 `recovery_orchestrator`는 `recovery_branch` 이벤트에 `phase: "validation_recovery"`를 쓴다. 이 phase는 **최종 검증 프레임**에 묶여 STEP10 메타·오버레이 범례에 노출된다.

별칭 `final_validation_failure` 등은 현재 이벤트에서 쓰이지 않는다. 추가 시 같은 프레임에 편입하거나 `_FRAME_ID_TO_EVENT_PHASES`만 확장하면 된다.

## `ui_frames` 행 필드 (서버)

- `event_indices`: 해당 타임라인 프레임과 연결된 이벤트 인덱스 (phase 매핑은 `solver_replay_frames.build_replay_ui_frames` 참고).
- `overlay_event_indices`: STEP10에서 강조할 이벤트 부분집합 — 현재 `recovery_branch`, `rollback`, `route_replaced` 종류.
- `pass3_layout_snapshots`: 같은 프레임 구간의 `pass3_layout_snapshot` 이벤트에서 추출한 `marker`, `layout_state_sha256`, 선택적 `transaction_id`.
- `computation_cycle_*`: UI 틱/stride 힌트 (메타 표시용).

## 이벤트 종류별 UI 의미 (v4 페이로드 한계)

| kind | 지도 좌표 | UI 권장 |
|------|-----------|---------|
| `recovery_branch` | 없음 (`validation_recovery_attempt` 등 메타) | 배지·범례·한 줄 요약 |
| `rollback` | 없음 (txn id 중심) | 메타·상태 |
| `route_replaced` | **v5+**: 페이로드·`replacements[]`에 `cells_removed` / `cells_added` (`[x,y]`), `cells_kept`, `transport_kind` (`shape_belt` \| `fluid_pipe`), `replacement_reason`; 이벤트 최상위는 행들의 집합(union) | 범례·카운트 + **지도 윤곽** ([`asteroid_optimizer.html`](../../django_apps/web/templates/web/asteroid_optimizer.html) `am-route-replay-*`) |
| `pass3_layout_snapshot` | 없음 (해시·marker) | `pass3` 프레임 범례·툴팁 |
| `map_diff_committed` 등 | v4에서 셀 목록 없음 (집계만) | 메타만 |

좌표 오버레이가 필요하면 이벤트 페이로드 확장 또는 계약 버전 상향으로 정의한다.

## 공간 오버레이와 `solver_summary`

- **P4 / 소프트 리페어**: `p4_reclaim_last_commit_route_cells`, `p4_reclaim_last_soft_protected_candidate_cells`, `p4_soft_replace_*_cells` 등은 웹의 `renderPlot` P4 그룹과 동일 계약이다.
- **프레임별 `summary`**: `finalize`가 넣는 키가 없으면 해당 스텝에서는 P4 윤곽이 비어 있을 수 있다 — 정상.

## Pass3 요약 필드 (최종 summary와 혼동 방지)

- `pass3_skipped`: Pass3 **블록이 실행되지 않음**일 때만 `True` (비자격·트레이스 조기 스킵).
- `pass3_reverted`: 실행 후 검증/가드 등으로 **맵이 원복**된 경우 `True`.
- `pass3_committed`: 내부 최소화 트레이스의 커밋 플래그와 정렬 (`p3_trace.pass3_committed`); 최종 레이아웃 수락은 `pass3_final_committed` / `pass3_map_accepted`로 본다.

## 참고 코드

- [`solver_replay_events.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_events.py) — 계약 주석
- [`solver_replay_frames.py`](../../django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_replay_frames.py) — `ui_frames` 생성
- [`asteroid_optimizer.html`](../../django_apps/web/templates/web/asteroid_optimizer.html) — `syncMapTimelineStep`, `renderPlot`
