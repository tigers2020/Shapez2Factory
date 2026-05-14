# 목표: Replay 타임라인 프레임과 §16.2 단계 정렬

## 배경

- 정본: `14_step10_replay_ui.md` §16.2 — Pass3 before/after, reclaim, post-reclaim Pass3 등 **단계 가시성**.
- 구현: `foundation/constants.py`의 `SOLVER_TIMELINE_FRAME_ORDER`에 P4 전용 프레임이 없고, 주석으로 Pass3 프레임에 흡수된다고만 설명된다.

## 현재 상태

- UI/소비자가 “reclaim 단계”를 타임라인 행으로 구분하기 어려울 수 있다.

## 목표 상태

- **A)** `SOLVER_FRAME_P4_RECLAIM` 등을 순서에 넣고 `build_final_solver_output` / 프론트가 해당 행을 렌더한다.
- **B)** 정본 §16.2에 “프레임 ID는 Pass3에 병합, 상세는 replay event phase”를 **정본 예외**로 명시한다.

## 작업 항목

1. `solver_replay_frames.py` / `asteroid_optimizer.html`이 실제로 어떤 `id`를 기대하는지 확인한다.
2. 프레임 추가 시 `SOLVER_REPLAY_CONTRACT_VERSION` 갱신 여부 결정.
3. 문서·CHANGELOG 한 줄.

## 검증

- `test_solver_replay_frames` 등 계약 테스트 갱신.

## 위험

- 계약 버전 상승 시 구버전 NDJSON UI 호환 정책 필요.

## 참고 코드

- `foundation/constants.py` (`SOLVER_TIMELINE_FRAME_ORDER`, `SOLVER_REPLAY_CONTRACT_VERSION`)
- `solver/solver_replay_frames.py`, `web/templates/web/asteroid_optimizer.html`
