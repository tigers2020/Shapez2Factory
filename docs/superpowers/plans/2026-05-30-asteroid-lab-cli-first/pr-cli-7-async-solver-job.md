# PR-CLI-7 — Async Solver Job (detach + polling + reap)

**Type:** contract change · implementation change · UI change  
**Status:** APPROVED (architecture review 2026-05-31)  
**Depends on:** PR-CLI-4 … PR-CLI-6 (subprocess_only + artifact ingest)  
**Scope:** HTTP `POST run-solver` + Lab UI only (management `run_solver` sync UX unchanged in P0)

---

## Approval

**Verdict:** Proceed with P0 → P1 → P2.

```text
P0 = detach subprocess + SolverRun RUNNING registry + HTTP 202 + status polling + reap
P1 = progress.jsonl (artifact-external)
P2 = SSE
```

Aligns with CLI-first: Django = job registry + artifact viewer; CLI = solver executor; DB = index/cache only.

---

## P0 core invariant (normative)

```text
P0 completion detection is artifact-validation-first, not process-exit-first.
```

| Signal | Role |
|--------|------|
| `Popen.returncode` / pid liveness | **Auxiliary** only (zombie cleanup, diagnostics) |
| Finalized artifact + manifest + hash validation | **Authoritative** completion |

**Success (all required):**

```text
artifact dir exists (<artifact_root>/<run_key>/)
+ manifest.json exists
+ lifecycle_status == ARTIFACT_WRITTEN
+ content hash validation pass (artifact_manifest_reader)
+ ingest_artifact_for_project success
```

**Failure (no ingest, no manifest rewrite):**

```text
max runtime timeout exceeded
OR no finalized manifest
OR validation fail
OR subprocess log fatal marker (typed; no free-form failure_reason)
```

Never ingest `.tmp/<run_key>` staging or partial dirs.

---

## Path separation (normative)

| Path | Purpose | ingest / UI |
|------|---------|-------------|
| `var/runs/.tmp/<run_key>/` | CLI internal staging (BA-5) | **Forbidden** |
| `var/runs/.live/<run_key>/` | P1 progress only (`progress.jsonl`) | **Forbidden** in P0; never ingest |
| `var/runs/<run_key>/` | Finalized immutable artifact | ingest **only** after `ARTIFACT_WRITTEN` |
| `var/runs/.subprocess_logs/<run_key>.log` | P0 status `log_tail` (sidecar) | read-only tail; not algorithm input |

---

## P0 forbidden

- Mid-run `replay_core.jsonl` read or SSR replay streaming (BA-4/BA-5)
- Parallel runs per project (see one-active-run)
- Duplicate reconcile logic in HTTP vs `run_solver_reap` (single function only)
- Rewriting `manifest.json` on ingest

P0 goal = **remove response blocking** only:

```text
POST 202 → GET status poll → on complete lazy replay fetch
```

---

## Single reconcile entry point

Both callers invoke the same function:

```text
reconcile_solver_run(run_id) -> ReconcileResult
```

| Caller | When |
|--------|------|
| `GET .../solver-runs/<id>/status/` | Every poll (inside transaction + lock) |
| `manage.py run_solver_reap` | Scan all `SolverRun.status == RUNNING` |

No second completion path.

### Locking and idempotency

Concurrent callers: UI poll, refresh, reap cron, admin.

```python
with transaction.atomic():
    run = SolverRun.objects.select_for_update().get(pk=run_id)
    if run.lifecycle_status in ("indexed", "succeeded", "failed"):
        return current_status  # no re-ingest
    # timeout check → maybe mark FAILED
    # artifact-validation-first completion → ingest once
```

Early return when terminal `lifecycle_status` or `status` in `COMPLETED`/`FAILED`/`CANCELLED` after successful ingest.

---

## P0 flow (authoritative)

### POST `/run-solver/`

1. **One-active-run guard** — same `project_id` with `status=RUNNING` → **409**
2. Create `SolverRun` (`RUNNING`, `started_at`, `run_key`, planned `artifact_root`)
3. `spawn_solver_subprocess_detached()` — `shell=False`, `sys.executable`, fixed cwd; **no wait**
4. Persist in `config_json`: `subprocess_pid` (optional), `spawned_at`, input paths, sidecar log path
5. **202** `{ ok, solver_run_id, run_key, status: "running", status_url }` — no replay/summary body

### GET `/solver-runs/<id>/status/`

1. `reconcile_solver_run(run_id)` under `select_for_update`
2. If still running: return `log_tail` from sidecar only (not artifact)
3. If reconcile completed: return `status`, `lifecycle_status`, `run_summary`, lazy replay handle fields

### `manage.py run_solver_reap`

1. `SolverRun.objects.filter(status=RUNNING)` (batch)
2. For each id: `reconcile_solver_run(id)` (same code path)

---

## Current state (baseline)

| Item | Today |
|------|-------|
| HTTP `run_solver` | Blocks until subprocess + ingest; JSON 200 |
| Lab UI | Single `fetch(POST)` until response |
| `SolverRun` row | Created at ingest only |
| CLI | Full stack → atomic finalize → `ARTIFACT_WRITTEN` |

Refs: [`solver_runtime_entry.py`](../../../../django_apps/asteroid_lab/services/solver_runtime_entry.py), [`public_pages.py`](../../../../django_apps/web/views/public_pages.py), [`artifact_ingest.py`](../../../../django_apps/asteroid_lab/services/artifact_ingest.py).

---

## Implementation map (P0)

| Step | Work | Files |
|------|------|-------|
| 1 | Registry + one-active-run guard | `solver_run_registry.py`, models usage |
| 2 | `spawn_solver_subprocess_detached` | `solver_subprocess_runner.py`, `subprocess_stream_tee.py` |
| 3 | `enqueue_solver_run_for_project` + **`reconcile_solver_run`** | `solver_runtime_entry.py` |
| 4 | POST 202 + GET status | `public_pages.py`, `urls.py` |
| 5 | `run_solver_reap` command | `management/commands/run_solver_reap.py` |
| 6 | Lab UI polling | `asteroid_miner_layout_lab.js` |

Settings:

| Name | Role |
|------|------|
| `ASTEROID_LAB_SOLVER_ASYNC_DEFAULT` | POST default 202 |
| `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` | reap timeout (not sync wait) |
| `ASTEROID_LAB_STATUS_LOG_TAIL_BYTES` | cap `log_tail` |

---

## Required tests (P0)

```text
- POST returns 202 and does not block on subprocess completion
- existing RUNNING run on same project returns 409
- partial .tmp artifact is never ingested
- finalized ARTIFACT_WRITTEN artifact is ingested once
- duplicate status polling does not double-ingest
- reap and status GET racing does not double-ingest (select_for_update)
- timeout marks FAILED without ingest
- failed validation marks FAILED without manifest rewrite
- completion uses artifact manifest, not returncode alone (returncode optional case)
```

Suggested paths:

- `tests/unit/asteroid_lab/test_solver_run_async_spawn.py`
- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`
- `tests/unit/asteroid_lab/test_run_solver_reap.py`
- `tests/integration/web/test_asteroid_miner_layout_solver_async.py`

---

## P1 / P2 (deferred)

**P1:** Core emits `var/runs/.live/<run_key>/progress.jsonl`; `GET .../events?after_seq=N`. Layer `emit_cli_line` during stack loop.

**P2:** `GET .../events/stream` (SSE) after polling stable.

`replay_core.jsonl` remains finalize-time only (BA-4/BA-5).

---

## Verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_solver_run_async_spawn.py tests/unit/asteroid_lab/test_reconcile_solver_run.py tests/unit/asteroid_lab/test_run_solver_reap.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver_async.py -v
python -m ruff check django_apps/asteroid_lab/services/solver_runtime_entry.py django_apps/web/views/public_pages.py
```

PR gate: `scripts/test_full.ps1` → ruff → mypy → black.

---

## Docs (on implement)

- [`documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md`](../../../../documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md)
- [`checklist.md`](checklist.md) — PR-CLI-7 section
- `structure.md` — `run_solver_reap`, status URL

---

## Risks

| Risk | Mitigation |
|------|------------|
| Detached pid unreliable | Artifact-first completion; pid auxiliary |
| Double ingest | `select_for_update` + terminal lifecycle guard |
| Parallel runs | 409 one-active-run per project in P0 |
| `.live` confused with artifact | Path denylist in ingest + tests |
