# STEP10 cycle replay NDJSON·API 정렬 (2026-05-13)

## 목적

- Replay NDJSON(`trace_event`)에 **`computation_cycle`(trace 단계 번호)** 과 주기적 **`replay_frame`** 을 기록한다.
- API `solver_replay`에 **`cycle_frames`** 를 추가해 UI 슬라이더가 패스 수(약 6)에 고정되지 않도록 한다.
- **`bundle_reject_invalid_stub` 등은 `event_type: candidate_reject`** 로 정규화하되, replay “프레임” 카운트에는 `replay_frame` 만 포함한다.

## 필드명 (고정)

- NDJSON `data` 및 trace 줄: 누적 단계 **`computation_cycle`** (한 `trace_event` 호출 = 1 증가).
- `replay_frame` 페이로드: 동일 시점의 단계 번호를 **`trace_computation_cycle`** 로도 보관(선택·디버그). 메모리 `replay_events` 정규화 후의 리스트 순번 `computation_cycle`과 혼동하지 않는다.

## UI (안 A)

- `solver_replay.cycle_frames` 가 비어 있지 않으면 통합 타임라인의 솔버 구간을 **`cycle_frames` 기반 합성 스텝**으로 대체한다.
- 각 합성 스텝은 `mining_map`(있으면)·`summary`(가능한 범위)·`id`를 갖는다. `mining_map` 이 없으면 직전에 유효했던 맵 또는 `map_timeline` 마지막 맵으로 carry-forward.

## 비범위

- 라우팅·Pass3·Reclaim·Recovery·검증 알고리즘 본경로 변경 없음.
- Debug NDJSON과 Replay NDJSON 분리 유지.

## 검증

- 단위: NDJSON 파서, `replay_frame` ≥ 11 synthetic, stub-only 폴백, debug 와이어 거절.
- `pytest` / `ruff` / `mypy` / `black`.

## 승인

구현은 본 문서 및 Cursor 플랜 합의 후 진행한다.
