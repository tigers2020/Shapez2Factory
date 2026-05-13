# ACTIVE: Replay NDJSON vs debug NDJSON 분리

- **상태**: ACTIVE (구현 진행)
- **목적**: `trace_event`는 replay 전용 경로에만 기록하고, `var/asteroid_mining_layout_debug`에는 action·진단만 남긴다.
- **정본 코드**: `django_apps/shapez_asteroid/services/asteroid_mining_layout/solver/solver_trace.py`
- **환경**: `SHAPEZ_SOLVER_REPLAY_DIR`(선택), `SHAPEZ_SOLVER_TRACE_PATH`(단일 replay 파일 오버라이드), `SHAPEZ_SOLVER_DEBUG_DIR`

승인: 채팅에서 플랜 구현 지시로 대체.
