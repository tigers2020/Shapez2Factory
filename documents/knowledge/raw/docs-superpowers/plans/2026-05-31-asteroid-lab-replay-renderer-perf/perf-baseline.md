# Renderer Perf — Budgets + Measurement Procedure

**Role:** perf contract for the PR-RENDER-* set. Budgets here are the oracle; recorded numbers live in
[`baseline-notes.md`](baseline-notes.md) (LOCK-1).

> Observability only. Browser perf traces and the optional `data-lab-perf-debug` counters are the same
> class as the server-side [`lab_perf_trace`](../../../../django_apps/asteroid_lab/observability/lab_perf_trace.py)
> JSONL — **never** an algorithm input (FD-1).

---

## Budgets (acceptance oracle)

| Metric | Budget | Scope |
|--------|--------|-------|
| rAF handler p95 | ≤ 16.7 ms | steady playback, reference map |
| rAF handler sustained violation | none > 32 ms back-to-back | 88-frame play-through |
| Forced reflow count | 0 | steady playback (post-RENDER-2) |
| Unchanged-frame touched DOM cells | 0 | RENDER-1 onward (LOCK-2) |
| Changed-frame touched DOM cells | ≤ changed token count + bounded housekeeping | RENDER-1 onward (LOCK-2) |
| `img.src` writes | only on cell token change | RENDER-1 onward |
| Bundle-bridge DOM create/remove per frame | 0 (pooled) | RENDER-3 onward |

Budgets are **not** retroactively softened. If a step cannot meet a budget, record the gap in
`baseline-notes.md` and treat it as the next PR's input — do not weaken the budget.

---

## Reference fixtures

| Slug / run | Why |
|------------|-----|
| `rttp-core-recovery-test-map` (88-frame replay, run id ~297/300) | heavy reference; `lab_replay_get` ~14MB payload observed in `lab_perf.jsonl` |
| a small `copy-import-*` run (13–27 frames) | low-frame sanity; confirms diff path does not regress tiny maps |

Server-side context already captured in
[`var/log/asteroid_lab_perf/lab_perf.jsonl`](../../../../var/log/asteroid_lab_perf/lab_perf.jsonl)
(`request_kind: lab_replay_get`, `payload_bytes`, `frame_count`). Use it for the `decoded payload size`
field; do not re-derive from the renderer.

---

## Chrome DevTools capture procedure (manual, RENDER-0)

1. Load the lab page for the reference slug; wait for replay surface mount (`#lab-replay-grid` populated).
2. DevTools → Performance → record.
3. Press play; let the full 88-frame timeline run once to completion (auto-pause at end).
4. Stop recording.
5. Read off:
   - **rAF median / p95**: filter Main thread for `requestAnimationFrame` handler durations; export to compute median + p95 (or eyeball top entries for p95).
   - **Forced reflow count**: count "Recalculate Style / Layout" entries flagged with the purple "forced reflow" warning during steady playback (exclude initial mount).
   - **`[Violation] requestAnimationFrame handler took Nms`**: count console violations and the max N.
6. **DOM node count**: in Console, `document.getElementById('lab-replay-grid').querySelectorAll('*').length`.
7. **full reset count / touched cell count**: enable the `data-lab-perf-debug` counter (added in RENDER-0 skeleton / RENDER-1) and read the logged per-frame touched-cell numbers; or, pre-instrumentation, infer full resets from `replayFrameNeedsFullGridReset` returning true (keyframes + ≥15% threshold).

Record one block per run in `baseline-notes.md`.

---

## Optional Playwright trace (RENDER-3+)

When manual capture becomes the bottleneck, a Playwright script may automate steps 1–5 (navigate, click
play, wait for end sentinel, dump `performance.getEntriesByType('measure')` from the `data-lab-perf-debug`
marks). This is observability tooling, kept out of the algorithm path. Not required to close RENDER-0.

---

## `lab_perf.jsonl` fields used here

| Field | Use |
|-------|-----|
| `payload_bytes` / `response_bytes` (`lab_replay_get`) | decoded payload size, LOCK-3 byte accounting |
| `frame_count` | frame count |
| `total_full_map_cells` | confirms overlay-heavy vs full-map-heavy frames |
| `replay_compose_ms` / `replay_cache_load_ms` | server-side cost; isolates client renderer cost |

These are server timings; the renderer budgets above are **client-side** and measured in the browser.
