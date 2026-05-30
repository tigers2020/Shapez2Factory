# PR-CLI-4 — Django Subprocess Mode + Artifact Ingest

**Type:** implementation change · contract change (settings flag)
**Depends on:** PR-CLI-3b (full pure CLI must exist to spawn)
**Enables:** PR-CLI-5
**Branch (suggested):** `feat/asteroid-cli-first-django-subprocess`

---

## Goal

Add `ASTEROID_LAB_SOLVER_MODE` to Django. In `subprocess` mode, `run-solver` spawns the CLI (BA-7),
ingests the resulting artifact directory (BA-5 post-`ARTIFACT_WRITTEN`), and writes ORM index/cache
fields only. `in_process` remains default fallback.

## Behavior contract

- `in_process` (default): current [`run_layer02_solver_for_project`](../../../../django_apps/asteroid_lab/services/solver_runtime_layer02.py) path unchanged.
- `subprocess`: spawn CLI, wait with timeout, validate manifest hashes, ingest → `SolverRun` index fields.
- DB never indexes partial artifacts; ingest only on `ARTIFACT_WRITTEN`.
- Manifest parsed by `artifact_manifest_reader.py` (BA-6 Option 1) — no core import in reader.

## Non-goals

- No DB demotion of replay yet (PR-CLI-5).
- No default flip to subprocess_only (PR-CLI-6).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`config/settings.py`](../../../../config/settings.py) | `ASTEROID_LAB_SOLVER_MODE` (default `in_process`) |
| Create | `django_apps/asteroid_lab/services/solver_subprocess_runner.py` | BA-7 subprocess invocation |
| Create | `django_apps/asteroid_lab/services/artifact_ingest.py` | post-manifest ingest → ORM index fields |
| Create | `django_apps/asteroid_lab/services/artifact_manifest_reader.py` | BA-6 Option 1 plain-JSON validator |
| Modify | [`services/solver_runtime_entry.py`](../../../../django_apps/asteroid_lab/services/solver_runtime_entry.py) | dispatch by mode |
| Modify | [`management/commands/run_solver.py`](../../../../django_apps/asteroid_lab/management/commands/run_solver.py) | `--subprocess` / `--artifact-dir` |
| Modify | web run-solver view (POST) | `solver_mode=subprocess` opt-in (staff/dev) |
| Create | `tests/unit/asteroid_lab/test_artifact_ingest.py` | ingest writes index only |
| Create | `tests/unit/asteroid_lab/test_artifact_manifest_reader.py` | no core import + validation |
| Create | `tests/unit/asteroid_lab/test_solver_subprocess_runner.py` | BA-7 args/timeout/traversal guard (mock subprocess) |
| Modify | [`tests/integration/web/test_asteroid_miner_layout_solver.py`](../../../../tests/integration/web/test_asteroid_miner_layout_solver.py) | `@override_settings(ASTEROID_LAB_SOLVER_MODE="subprocess")` |

---

## Subprocess runner (BA-7)

```python
result = subprocess.run(
    [sys.executable, "-m", "shapez2_factory.interfaces.cli.asteroid_solve", "run",
     "--decoded-json", str(decoded_path),
     "--snapshot", str(snapshot_path),
     "--artifact-root", str(artifact_root),
     "--run-key", run_key],
    shell=False,
    cwd=str(SOLVER_CWD),          # fixed allowed root
    capture_output=True,
    timeout=BUDGET_MS / 1000 + ARTIFACT_OVERHEAD_S,
    text=True,
)
# write result.stdout/stderr → <artifact>/logs/subprocess.log
# map result.returncode → SolverRuntimeEntryErrorCode
```

Path-traversal guard (BA-7 + guard C): reuse `run_key_safety.resolve_artifact_dir` from PR-CLI-3a on the
Django side too — `run_key` no separators / not `.`/`..` / matches `^[A-Za-z0-9._-]+$`, and resolved dir
must stay under the configured allowed root. Django must not trust a caller-supplied `artifact_root`.

## artifact_ingest (BA-5)

```text
1. read manifest via artifact_manifest_reader
2. assert manifest.lifecycle_status == ARTIFACT_WRITTEN  (only ever this value in manifest)
3. re-hash payload files; compare manifest.content_hashes (excludes manifest.json); fail-closed on mismatch
4. write SolverRun index fields: run_key, artifact_root, error_code,
   solver_summary cache, replay pointer (path) — NOT recompute solver
5. advance DB SolverRun.lifecycle_status: INDEXED → SUCCEEDED
```

**Lifecycle authority (normative):** `INDEXED`/`SUCCEEDED` are written **only** to the DB `SolverRun` row.
Ingest **must never rewrite `manifest.json`** — the manifest stays `ARTIFACT_WRITTEN` forever. This keeps
`validate-artifact` (which expects exactly `ARTIFACT_WRITTEN`) consistent with ingest progression.

## Tasks

- [ ] **Step 1:** Add setting + mode dispatch in `solver_runtime_entry`.
- [ ] **Step 2 (TDD):** `artifact_manifest_reader` validation + no-core-import test (AST assert).
- [ ] **Step 3 (TDD):** `solver_subprocess_runner` — mock `subprocess.run`; assert `shell=False`, list args, timeout set, traversal rejected.
- [ ] **Step 4 (TDD):** `artifact_ingest` — hash mismatch fails closed; partial (not ARTIFACT_WRITTEN) rejected; index-only writes.
- [ ] **Step 5:** Wire HTTP/management opt-in flags.
- [ ] **Step 6:** Integration test subprocess mode end-to-end (small fixture).
- [ ] **Step 7:** ruff + mypy + full gate.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/asteroid_lab/test_artifact_manifest_reader.py tests/unit/asteroid_lab/test_solver_subprocess_runner.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v
python -m mypy django_apps config src
```

## Risks

- Windows subprocess timeout/kill — ensure `timeout` + cleanup of `.tmp` on failure.
- `invariant:` DB rows ≠ algorithm input — ingest must not feed data back into solver.
- Manifest reader must stay core-free; add AST test to enforce BA-6.
- Concurrency: two runs same `run_key` — lock or `replace_existing_run` semantics; reject partial.

## Done criteria

- Both modes work; subprocess produces + ingests artifacts safely; index-only DB writes; integration green.
