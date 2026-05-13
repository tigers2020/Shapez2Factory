# 목표: Replay·NDJSON·`solver_summary`는 trace/debug/report 계층 — 알고리즘 입력 아님

## 배경

- 정본: `14_step10_replay_ui.md` §16 — replay·trace 스키마; 감사 관점에서 라우팅 핵심은 **맵·placement·routing_state** 등이 입력이다.
- NDJSON·이벤트 스트림은 재현·UI·디버그용이다.

## 현재 상태

- `run_solver_timeline_pipeline`은 `decoded`→`build_map_timeline` 등으로 핵심 입력을 구성하고, `replay_events`는 부수적으로 쌓인다.
- `layout_preserve_hard_gate` 등은 **요약 필드·타임라인 프레임**을 고치며 NDJSON 파일을 “읽어” STEP4에 넣지는 않는다.
- **디스크**: `django_apps/.../solver_trace.py`가 `trace_event`(STEP10 스트림)을 `var/asteroid_mining_layout_replay/`(`{run_id}.ndjson`, `replay_latest.ndjson`)에만 쓰고, `debug_log_event`·`run_start`/`run_end` 등은 `var/asteroid_mining_layout_debug/`에만 쓴다(구버전처럼 한 파일에 `kind: trace`를 섞지 않음). 환경 변수: `SHAPEZ_SOLVER_REPLAY_DIR`, `SHAPEZ_SOLVER_TRACE_PATH`(단일 replay 파일), `SHAPEZ_SOLVER_DEBUG_DIR`.

## 목표 상태

- 어떤 함수도 **디스크상 NDJSON**을 라우팅 입력으로 읽지 않는다는 것을 아키텍처 불변식으로 문서화한다(디버그 전용 CLI가 있다면 명시적으로 격리).
- `solver_summary`의 필드가 다음 패스의 **분기 입력**이 되기 시작하면(피드백 루프), 계층을 분리하거나 필드에 `derived_` 접두를 붙인다.

## 작업 항목

1. `grep`으로 `ndjson`·`replay_events`·`solver_summary`를 STEP4/Pass3 **입력**으로 쓰는 경로 조사.
2. copy-preview·optimizer API가 클라이언트에 넘기는 payload에서 “재실행 입력” vs “표시용 trace” 경계를 OpenAPI/주석에 명시.
3. 계약 버전(`SOLVER_REPLAY_CONTRACT_VERSION`) 변경 시 “알고리즘 입력 불변” 체크리스트 항목 추가.

## 검증

- 정적: solver 핵심 모듈이 `solver_replay_events`를 읽기만 하고 분기에 쓰지 않는지(emit만 허용 등) 정책 결정.

## 참고 코드

- `solver_pipeline/recovery_orchestrator.py`, `solver/solver_replay_events.py`, `solver/solver_replay_frames.py`
- `django_apps/shapez_asteroid/views.py` (API payload)
