# Protected Corridor Overlay MVP (2026-05-10)

## 목적

STEP4 `routing_state` 기반 **hard / soft / candidate** 보호 코리도를 **읽기 전용**으로 시각화한다. 라이브 스트리밍·WebSocket·delta 전송은 범위 밖이다.

## 페이로드

- `solver_replay.ui_frames[i].protected_corridors`: `{ hard, soft, candidate, counts }` — 좌표는 `[x, y]` (x≠0), `counts`는 타일 개수.
- 타임라인 인덱스별 값은 **해당 프레임까지의 최신 `summary.routing_state`**를 사용한다(STEP4 이후 carry-forward).
- `copy-preview` 최종 `summary.replay_protected_corridor_counts`: 솔버 요약의 `routing_state`에서 동일 집계를 병합한다.

## UI

- 옵션: **「보호 코리도 표시(읽기 전용)」** 체크박스.
- 맵: candidate → soft → hard 순으로 **윤곽(stroke)**만 그린다(채운 transport 타일과 분리).
- `replayMeta` / 디코드 요약: 코리도 개수 한 줄.

## 검증

- `test_solver_replay_corridors.py`, `test_copy_preview` 병합, `SOLVER_REPLAY_CONTRACT_VERSION` 6.

## 후속(플랜 밖)

- Phase B: 코리도 수명(승격·제거) 이벤트와의 동기.
- Phase C: 툴팁에 `transaction_id` 등.
