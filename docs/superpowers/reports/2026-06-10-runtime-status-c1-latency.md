# Runtime Status C1 Latency Report (2026-06-10)

## Environment

- Branch: `pr-cli-7-runtime-status-ux-c1` (from C1 commits on `master`)
- Run: Asteroid Mining Lab — Greenfield Solver Workspace, Run #464
- Measurement: Chrome DevTools Network tab (user capture)

## Before C1 (user capture)

| Metric | Value | Notes |
|--------|-------|-------|
| running `status/` | 14–22 ms, 0.6 kB | Fast poll loop |
| final `status/` pmax | **~50.38 s**, 2.1 kB | ingest + replay iterate + cache warm compose |
| first `lab-replay/` | ~892 ms, 255 kB | After terminal status |

## After C1 Browser Measurement

| Metric | Before | After C1 | Notes |
|--------|--------|----------|-------|
| running `status/` | 14–22 ms | 14–20 ms | stable |
| final `status/` | ~50.38 s | **~236 ms**, 2.1 kB | status hot path fixed |
| first `lab-replay/` | ~892 ms | **~45.45 s**, 237 kB | compose moved to lab-replay path |

### Removed from status hot path

1. `_warm_lab_replay_cache_after_artifact_ingest` when `ingest_options=STATUS_RECONCILE_INGEST_OPTIONS`
2. `iter_replay_core_frames` full scan when `summarize_replay_frames=False`

### UI observability

- `log_tail` rendered during running polls
- Elapsed seconds + `finalizing artifacts…` after 3s in-flight status fetch
- Replay timeline reached 37/37; run #464 completed with stack success

## Conclusion

C1 achieved its goal: **status polling hot path no longer blocks ~50s on replay compose/cache warm.**

```text
Before: last status/ ≈ 50.38s (blocking)
After:  final status/ ≈ 236ms
        lab-replay/   ≈ 45.45s (intentional lazy compose path)
```

**C2 is not triggered by status latency.** Final `status/` (~236 ms) is below the 500 ms C2 threshold.

A separate **lab-replay first compose latency** investigation is recommended if ~45 s first replay fetch is unacceptable for UX. C2 (deferred ingest / `phase` fields) does not address `lab-replay/` compose time and should remain deferred.
