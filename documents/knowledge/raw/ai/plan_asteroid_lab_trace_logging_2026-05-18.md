# Asteroid Lab structured trace logging plan

## Status

- Date: 2026-05-18
- Scope: `LOG-1` baseline + priority boundary logs
- Principle: trace JSONL is output/debug artifact; do not read as solver/algorithm input.

## Implementation scope

- `AsteroidLabTraceLogger`: per-`run_id` stage JSONL writer, `summary.json`, max event/byte cap.
- settings flag: `ASTEROID_LAB_TRACE_LOG_ENABLED`, `ASTEROID_LAB_TRACE_LOG_DIR`, cap/sample config.
- decode logging: raw blueprint summary, raw X/Y -> server X/Y projection sample, `raw_x == 0`/missing server coord diagnostic.
- cleanup logging: transport/building removal summary, `cell_removed_or_retyped` sample, wall evidence flag.
- reconstruction logging: copy existing `ReconstructionTraceCollector` events to run JSONL.
- optimization input logging: Server X/Y membership summary and sample classification.

## Forbidden

- Do not read trace files as solver input.
- Do not store full copy_code/raw JSON by default.
- logging on/off must not change solver results.
- Do not grant raw/world coord conversion authority to optimization core.

## Remaining follow-up scope

- candidate/probe/commit/validation detail event expansion.
- replay/response payload byte attribution expansion.
- Wire HTTP request path/method/accept_json at view boundary directly.
