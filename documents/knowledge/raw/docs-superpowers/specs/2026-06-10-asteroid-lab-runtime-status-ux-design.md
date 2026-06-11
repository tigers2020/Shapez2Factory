# Asteroid Lab Runtime Status UX — P0.5 Design

**Status:** APPROVED (brainstorming 2026-06-10)  
**Date:** 2026-06-10  
**Scope:** Lab Run Solver async status polling UX (PR-CLI-7 P0 extension)  
**Parent plan:** [`../plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`](../plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md)  
**Implementation order:** **C1 first** → measure → **C2 only if blocking remains**

---

## Problem

Network evidence and code review show the Run Solver UI appears frozen for ~50s with no progress
feedback. This is **not** a missing HTTP streaming bug. PR-CLI-7 P0 is **polling**, not SSE.

Root causes (confirmed):

1. **UI gap:** `GET status/` returns `log_tail`, and the poll loop stores it, but
   `renderReplayRunStatus` displays only `run: running…` and ignores `log_tail`.
2. **Status blocking:** The poll that detects artifact completion runs
   `reconcile_solver_run → ingest_artifact_for_project` synchronously inside `GET status/`, including
   replay_core full iteration (`_lab_replay_manifest_summary`) and replay cache warm
   (`_warm_lab_replay_cache_after_artifact_ingest` → `build_lab_replay_frames_for_project`).
3. **Sequential poll:** `pollSolverRunStatus` awaits each `fetch` before scheduling the next tick;
   a long final `status/` blocks all further polls and UI updates.

Typical timeline (observed):

```text
run-solver/       202   ~470 ms
status/ × N       200   14–22 ms   0.6 kB   (running)
last status/      200   ~50 s      2.1 kB   (ingest + compose)
lab-replay/       200   ~892 ms    255 kB
```

---

## Non-goals

- SSE (`GET .../events/stream`) — P2 deferred
- `progress.jsonl` structured progress — P1 deferred
- Live replay frame streaming — forbidden (BA-4/BA-5; finalize-time only)
- Solver semantics changes
- Moving replay assembly authority out of Django viewer compose / assembler path
- Using replay or debug artifacts as solver input

---

## Frozen decisions

1. **P0 polling contract remains.** No switch to HTTP streaming in this work.
2. **Existing `status` enum preserved** for backward compatibility:
   `running | succeeded | failed` (and existing terminal values tests rely on). Do **not** introduce
   `status: completed` as a new contract value.
3. **`lab-replay/` remains the sole lazy compose path** for renderable frames after C1.
4. **Replay is output-only.** `log_tail` is subprocess sidecar observability, not algorithm input.

---

## Status response contract

### C1 (no new fields required)

Existing body unchanged. UI consumes `log_tail` and adds client-side elapsed / long-poll heuristic.

### C2 (additive fields only)

When C1 measurement shows `status/` blocking remains unacceptable, add:

```json
{
  "ok": true,
  "solver_run_id": 123,
  "status": "running | succeeded | failed",
  "lifecycle_status": "...",
  "phase": "solver_running | finalizing | ready | failed",
  "log_tail": "...",
  "replay_ready": false,
  "validation_passed": false,
  "run_summary": null,
  "error_code": null,
  "message": null
}
```

| Field | Contract |
|-------|----------|
| `status` | Existing lifecycle compatibility field. Existing UI and tests MUST NOT break. |
| `phase` | Additive UX / observability only. Omitted in C1; clients fall back to `status`. |
| `replay_ready` | Whether `GET lab-replay/` may be requested (C2). **Not** “cache exists”, “frames pre-composed”, or “cache warm complete”. Means terminal success + ingest indexed per existing contract. |
| `log_tail` | Sidecar tail from `var/runs/.subprocess_logs/<run_key>.log`. Read-only; not solver input. |

### Phase semantics (C2)

| `phase` | `status` | `replay_ready` | Meaning |
|---------|----------|----------------|---------|
| `solver_running` | `running` | `false` | Subprocess active; artifact may be incomplete. |
| `finalizing` | **`running`** | `false` | Manifest `ARTIFACT_WRITTEN` detected; ingest/index in progress. |
| `ready` | `succeeded` | `true` | Terminal success; `lab-replay/` fetch allowed. |
| `failed` | `failed` | `false` | Terminal failure. |

**Critical:** While `phase=finalizing`, **`status` MUST remain `running`** so existing UI logic
(`status !== "running"` → terminal / lab-replay fetch) does not fire early.

---

## Server boundary split

### Forbidden inside `GET status/` (normative)

```text
✗ replay_core.jsonl full iterate for compose
✗ build_lab_replay_frames_for_project
✗ replay cache warm (persist_composed_replay_for_run_id)
✗ heavy ORM ingest unless proven p99 < 500 ms in measurement
```

### Allowed inside `GET status/` (C1)

```text
✓ tail_log_text (sidecar log_tail)
✓ manifest detect (read_verified_artifact_manifest gate)
✓ reconcile_solver_run fast paths (timeout, fatal log marker)
✓ minimal ingest index fields required for terminal status (if measured < 500 ms p99)
```

### Compose authority

```text
GET status/     → run state + log_tail (+ phase in C2)
GET lab-replay/ → load cache OR compose on miss (unchanged sole compose path)
```

Replay timeline assembly stays in the viewer compose / assembler stack. Layers do not gain UI
progress authority.

---

## C1 implementation scope (ship first)

### Frontend (`asteroid_miner_layout_lab.js`)

1. Render `log_tail` below run status during polling.
   - `textContent` or `<pre>` only — **no `innerHTML`**.
   - Cap lines/chars (e.g. last 20 lines or `ASTEROID_LAB_STATUS_LOG_TAIL_BYTES` mirror).
   - While a poll is in-flight, **keep displaying the previous tail** (no blank flash).
2. Elapsed timer while run in flight.
3. Long-poll heuristic: **before** awaiting `status/` fetch, start a client-side timer. If the same
   request is still pending after ~3s, update status text to `run: finalizing artifacts…` while
   preserving the previous `log_tail`. Clear the timer when fetch resolves. Do **not** overlap polls
   or shorten poll interval.

### Backend

1. When `ingest_artifact_for_project` is invoked from `GET status/` reconcile, it **MUST NOT**
   warm replay cache or compose replay frames. Other explicit/offline ingest paths (e.g. sync
   `run_solver_runtime_for_project`) may keep cache-warm behavior via an options parameter
   (e.g. `warm_replay_cache=True` default).
2. Hot-path manifest summary must be **O(1) or bounded**. Do **not** full-scan `replay_core.jsonl`
   for parse, validation, line count, or `frame_count`. Allowed: manifest metadata only, stored
   artifact metadata, bounded head/tail sample. Forbidden: full JSONL parse, full line count,
   `frame_count` computed by scanning `replay_core.jsonl`.
3. Re-measure latency and document three metrics: running `status/` p99, final `status/` p99/pmax,
   first `lab-replay/` p99/pmax (may increase after cache-warm removal; document separately).

### C1 acceptance

| Gate | Target |
|------|--------|
| Running `status/` | p99 < 100 ms |
| Final `status/` | Meaningful reduction from ~50 s baseline (document measured p99/pmax) |
| UI | `log_tail` visible during running polls |
| `lab-replay/` | Cache-miss compose allowed; first-fetch latency measured and documented |
| Contracts | No SSE, no progress.jsonl, no live replay frames |

**C1 scope guard:**

```text
C1 must not introduce overlapping polls, SSE, progress.jsonl, phase fields, or live replay frames.
C1 only makes polling observable and removes replay compose/cache warm from the status hot path.
```

---

## C2 implementation scope (only if C1 insufficient)

Trigger: final `status/` p99 still > 500 ms or UX still shows multi-second freeze.

1. Add `phase` and `replay_ready` to status body.
2. On manifest `ARTIFACT_WRITTEN` while row still `RUNNING`:
   - Persist `finalizing` marker.
   - Enqueue ingest via reap / background worker (same `reconcile_solver_run` idempotency).
   - Return immediately: `status=running`, `phase=finalizing`, `replay_ready=false`.
3. After ingest completes: `status=succeeded`, `phase=ready`, `replay_ready=true`.
4. UI gates `lab-replay/` fetch on `replay_ready` (C2) or existing terminal status (C1 fallback).

```text
manifest ARTIFACT_WRITTEN detected
  ↓
finalizing marker stored
  ↓
ingest job enqueue (reap / worker) — NOT blocking status response
  ↓
status/ returns phase=finalizing immediately
  ↓
ingest completes → phase=ready
```

Locking: retain `select_for_update` + idempotent ingest (PR-CLI-7). No double-ingest under
concurrent poll + reap.

---

## UI display (C1 + C2)

```text
run: running…
[recent solver log tail]

run: finalizing artifacts…    ← phase or >3s heuristic
[recent solver log tail]
```

Goal: evidence the run is **not stuck**, not a fake progress bar.

---

## Error handling

- Timeout → `status=failed`, appropriate `error_code` (existing reconcile paths).
- Validation failure → `failed`, no manifest rewrite (existing).
- `lab-replay/` fetch after terminal success → existing `replay_fetch_failed` path.
- Ingest race (C2) → idempotent reconcile; terminal early-return when already indexed.

---

## Tests

### C1

- Unit: ingest no longer calls cache warm from reconcile path (mock assert).
- Unit: `_lab_replay_manifest_summary` does not full-iterate on hot path.
- Integration: running status returns quickly with `log_tail`.
- Optional perf: document before/after status latency on representative artifact.

### C2 (if shipped)

- `phase=finalizing` while `status=running`; UI must not early-fetch lab-replay.
- Concurrent status + reap → single ingest.
- `replay_ready=true` only after terminal ingest success.

---

## Risks

| Risk | Mitigation |
|------|------------|
| First `lab-replay/` slower after cache warm removal | Expected; acceptable per measurement |
| “Lightweight ingest” still slow | C1 measures; C2 defers ingest off status thread |
| `phase` breaks existing clients | Additive only; `status` unchanged during finalizing |
| Replay authority drift to UI | Compose stays in `lab-replay/` / viewer compose only |

---

## Deferred

| Item | Phase |
|------|-------|
| `progress.jsonl` | P1 (PR-CLI-7) |
| SSE | P2 (PR-CLI-7) |
| Live replay frame streaming | Forbidden |

---

## References

- [`pr-cli-7-async-solver-job.md`](../plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md)
- `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` — `pollSolverRunStatus`, `renderReplayRunStatus`
- `django_apps/web/views/public_pages.py` — status + lab-replay endpoints
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` — `reconcile_solver_run`
- `django_apps/asteroid_lab/services/artifact_ingest.py` — ingest + cache warm
