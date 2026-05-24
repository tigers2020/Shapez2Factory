# Asteroid Lab structured trace logging checklist

- [x] Implement `AsteroidLabTraceLogger` / JSONL writer / `summary.json`
- [x] Add `ASTEROID_LAB_TRACE_LOG_ENABLED` and cap/sample settings
- [x] Add decode raw/projection summary events
- [x] Add cleanup transport/building removal events
- [x] Add reconstruction trace collector -> JSONL copy
- [x] Add OptimizationInput Server X/Y membership summary/sample events
- [x] Add logging on/off result identity tests
- [x] Add static test that trace log is not read as solver input
- [ ] Expand candidate/probe/commit/validation detail events
- [ ] Expand replay/response payload byte attribution
