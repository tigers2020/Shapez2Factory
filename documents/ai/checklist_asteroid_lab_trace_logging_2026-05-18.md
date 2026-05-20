# Asteroid Lab structured trace logging checklist

- [x] `AsteroidLabTraceLogger` / JSONL writer / `summary.json` 구현
- [x] `ASTEROID_LAB_TRACE_LOG_ENABLED` 및 cap/sample settings 추가
- [x] decode raw/projection summary 이벤트 추가
- [x] cleanup transport/building removal 이벤트 추가
- [x] reconstruction trace collector -> JSONL 복사 추가
- [x] OptimizationInput Server X/Y membership summary/sample 이벤트 추가
- [x] logging on/off 결과 동일성 테스트 추가
- [x] trace log를 solver 입력으로 읽지 않는 정적 테스트 추가
- [ ] candidate/probe/commit/validation 상세 이벤트 확장
- [ ] replay/response payload byte attribution 확장
