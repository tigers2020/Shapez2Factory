# Runtime Status C1 Latency Report (2026-06-10)

## Environment

- Branch: `master` (C1 commits `e6fe0979` … `3ce44add` + cherry-picks)
- Measurement method: user Network tab capture (before) + unit/integration timing on fake artifact (after structural change)
- Representative artifact: PR-CLI-7 test fixture (`_write_artifact` single-frame replay)

## Before C1 (user capture)

| Metric | Value | Notes |
|--------|-------|-------|
| running `status/` | 14–22 ms, 0.6 kB | Fast poll loop |
| final `status/` pmax | **~50.38 s**, 2.1 kB | ingest + replay iterate + cache warm compose |
| first `lab-replay/` | ~892 ms, 255 kB | After terminal status |

## After C1 (structural)

| Metric | Value | Notes |
|--------|-------|-------|
| running `status/` | Unchanged (~ms) | `tail_log_text` only |
| final `status/` (fake artifact integration) | **<1 s** in `test_http_status_complete_does_not_warm_replay_cache` | No `build_lab_replay_frames_for_project` on status path |
| first `lab-replay/` | Expected **≥ before** on cache miss | Compose deferred to `lab-replay/` only |

### Removed from status hot path

1. `_warm_lab_replay_cache_after_artifact_ingest` when `ingest_options=STATUS_RECONCILE_INGEST_OPTIONS`
2. `iter_replay_core_frames` full scan when `summarize_replay_frames=False`

### UI observability (no latency change, UX change)

- `log_tail` rendered during running polls
- Elapsed seconds + `finalizing artifacts…` after 3s in-flight status fetch

## Conclusion

C1 removes the dominant **replay compose + JSONL scan** work from the terminal `status/` request. The ~50s blocking observed before should drop to ingest/ORM-bound time only.

**C2 trigger:** Re-measure final `status/` p99 on a **production-sized** artifact after deploy. If p99 > 500 ms, implement deferred ingest (`phase=finalizing`) per spec C2.

**Manual follow-up:** Run one real solver in browser; confirm Network tab shows:

1. Running polls with visible log tail in UI
2. Final `status/` no longer ~50s
3. First `lab-replay/` may be slower — acceptable
