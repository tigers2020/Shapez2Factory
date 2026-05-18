# Asteroid Lab structured trace logging plan

## 상태

- 날짜: 2026-05-18
- 범위: `LOG-1` 기반 + 우선 경계 로그
- 원칙: trace JSONL은 output/debug artifact이며 solver/algorithm 입력으로 읽지 않는다.

## 구현 범위

- `AsteroidLabTraceLogger`: `run_id`별 stage JSONL writer, `summary.json`, max event/byte cap.
- settings flag: `ASTEROID_LAB_TRACE_LOG_ENABLED`, `ASTEROID_LAB_TRACE_LOG_DIR`, cap/sample 설정.
- decode logging: raw blueprint summary, raw X/Y -> server X/Y projection sample, `raw_x == 0`/missing server coord diagnostic.
- cleanup logging: transport/building removal summary, `cell_removed_or_retyped` sample, wall evidence 여부.
- reconstruction logging: 기존 `ReconstructionTraceCollector` 이벤트를 run JSONL로 복사.
- optimization input logging: Server X/Y membership summary와 sample classification.

## 금지

- trace 파일을 solver 입력으로 읽지 않는다.
- full copy_code/raw JSON을 기본 저장하지 않는다.
- logging on/off가 solver 결과를 바꾸면 안 된다.
- optimization core에 raw/world 좌표 변환 권한을 새로 주지 않는다.

## 남은 후속 범위

- candidate/probe/commit/validation 세부 이벤트 확장.
- replay/response payload byte attribution 확장.
- HTTP request path/method/accept_json을 view boundary에서 직접 연결.
