# Asteroid Lab Runtime Status UX — C1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PR-CLI-7 async Run Solver polling observable (log tail + elapsed/finalizing hint) and remove replay compose/cache warm from the `GET status/` hot path without changing solver semantics.

**Architecture:** C1 is a P0.5 UX fix only. Frontend renders existing `log_tail` safely and shows client-side progress during long in-flight status polls. Backend adds `ArtifactIngestOptions` so reconcile-driven ingest disables cache warm and O(1) replay summary; offline/sync ingest keeps default warm behavior. `lab-replay/` remains sole lazy compose path.

**Tech Stack:** Django 5, vanilla JS (`asteroid_miner_layout_lab.js`), pytest, existing artifact/reconcile services.

**Spec:** [`../specs/2026-06-10-asteroid-lab-runtime-status-ux-design.md`](../specs/2026-06-10-asteroid-lab-runtime-status-ux-design.md)

**C1 scope guard (normative):**

```text
C1 must not introduce overlapping polls, SSE, progress.jsonl, phase fields, or live replay frames.
C1 only makes polling observable and removes replay compose/cache warm from the status hot path.
```

---

## File map

| File | Responsibility |
|------|----------------|
| `django_apps/web/templates/web/asteroid_miner_layout_solver.html` | Add `#lab-replay-run-log` panel below status line |
| `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` | Log tail render, cap, elapsed timer, long-poll pending UI |
| `django_apps/asteroid_lab/services/artifact_ingest.py` | `ArtifactIngestOptions`; conditional warm + O(1) summary |
| `django_apps/asteroid_lab/services/solver_run_reconcile.py` | Pass status-hot-path ingest options from `_attempt_artifact_ingest` |
| `tests/unit/asteroid_lab/test_lab_runtime_status_ux.py` | JS contract + UI wiring tests |
| `tests/unit/asteroid_lab/test_artifact_ingest.py` | Options behavior + warm-path regression |
| `tests/unit/asteroid_lab/test_reconcile_solver_run.py` | Reconcile does not warm/scan on status path |
| `docs/superpowers/reports/2026-06-10-runtime-status-c1-latency.md` | Before/after latency measurements |

**Unchanged by C1:** `solver_runtime_entry.py` sync ingest keeps default `warm_replay_cache=True`; `public_pages.py` lab-replay endpoint; poll interval (1500 ms); sequential poll (no overlap).

---

### Task 1: UI log_tail panel + safe rendering

**Files:**
- Modify: `django_apps/web/templates/web/asteroid_miner_layout_solver.html:493` (after status `<p>`)
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`renderReplayRunStatus`, helpers)
- Create: `tests/unit/asteroid_lab/test_lab_runtime_status_ux.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/asteroid_lab/test_lab_runtime_status_ux.py
"""Lab Run Solver runtime status UX (C1): log tail panel contract."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_lab_template_has_replay_run_log_panel() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 'id="lab-replay-run-log"' in html


def test_lab_js_renders_log_tail_with_text_content_only() -> None:
    js = JS.read_text(encoding="utf-8")
    assert "function truncateLabStatusLogTail" in js
    assert "function renderReplayRunLogTail" in js
    assert 'getElementById("lab-replay-run-log")' in js
    assert ".textContent" in js[js.index("function renderReplayRunLogTail") : js.index("function renderReplayRunStatus")]
    assert "innerHTML" not in js[js.index("function renderReplayRunLogTail") : js.index("function renderReplayRunStatus")]


def test_render_replay_run_status_uses_log_tail_when_running() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function renderReplayRunStatus") : js.index("function getCookie")]
    assert "renderReplayRunLogTail" in block
    assert "feedback.log_tail" in block or "log_tail" in block
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_runtime_status_ux.py -v`

Expected: FAIL — `lab-replay-run-log`, `truncateLabStatusLogTail`, etc. missing.

- [ ] **Step 3: Add template log panel**

In `asteroid_miner_layout_solver.html`, immediately after the `lab-replay-run-status` paragraph:

```html
<pre
  id="lab-replay-run-log"
  class="mt-1 max-h-32 overflow-y-auto whitespace-pre-wrap font-mono text-[10px] leading-snug text-slate-400/90 hidden"
  aria-live="polite"
></pre>
```

- [ ] **Step 4: Add JS helpers and wire `renderReplayRunStatus`**

In `asteroid_miner_layout_lab.js`, above `renderReplayRunStatus`:

```javascript
  const LAB_STATUS_LOG_TAIL_MAX_LINES = 20;
  const LAB_STATUS_LOG_TAIL_MAX_CHARS = 4096;

  function truncateLabStatusLogTail(raw) {
    const text = typeof raw === "string" ? raw : "";
    if (!text) {
      return "";
    }
    let capped = text;
    if (capped.length > LAB_STATUS_LOG_TAIL_MAX_CHARS) {
      capped = capped.slice(-LAB_STATUS_LOG_TAIL_MAX_CHARS);
    }
    const lines = capped.split(/\r?\n/);
    if (lines.length > LAB_STATUS_LOG_TAIL_MAX_LINES) {
      return lines.slice(-LAB_STATUS_LOG_TAIL_MAX_LINES).join("\n");
    }
    return capped;
  }

  function renderReplayRunLogTail(tailText) {
    const logEl = document.getElementById("lab-replay-run-log");
    if (!logEl) {
      return;
    }
    const display = truncateLabStatusLogTail(tailText);
    if (!display) {
      logEl.textContent = "";
      logEl.classList.add("hidden");
      return;
    }
    logEl.textContent = display;
    logEl.classList.remove("hidden");
  }
```

Update `renderReplayRunStatus` running branch:

```javascript
    if (feedback.running === true) {
      const pendingFinalize =
        feedback.pending_finalize === true || feedback.phase_hint === "finalizing";
      const elapsed =
        typeof feedback.elapsed_seconds === "number" && feedback.elapsed_seconds >= 0
          ? " (" + String(Math.floor(feedback.elapsed_seconds)) + "s)"
          : "";
      runEl.textContent = pendingFinalize
        ? "run: finalizing artifacts…" + elapsed
        : "run: running…" + elapsed;
      if (typeof feedback.log_tail === "string" && feedback.log_tail) {
        renderReplayRunLogTail(feedback.log_tail);
      }
      return;
    }
```

On terminal/error paths, hide log panel:

```javascript
    renderReplayRunLogTail("");
```

(place at start of non-running branches in `renderReplayRunStatus`)

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_runtime_status_ux.py -v`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add django_apps/web/templates/web/asteroid_miner_layout_solver.html \
  django_apps/web/static/web/js/asteroid_miner_layout_lab.js \
  tests/unit/asteroid_lab/test_lab_runtime_status_ux.py
git commit -m "feat(lab): render solver status log tail during async run"
```

---

### Task 2: Elapsed timer + long-poll pending indicator

**Files:**
- Modify: `django_apps/web/static/web/js/asteroid_miner_layout_lab.js` (`pollSolverRunStatus`, run button handler)
- Modify: `tests/unit/asteroid_lab/test_lab_runtime_status_ux.py`

- [ ] **Step 1: Write the failing test**

Append to `test_lab_runtime_status_ux.py`:

```python
def test_poll_solver_run_status_uses_pending_finalize_timer() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function pollSolverRunStatus") : js.index("const runSolverBtn")]
    assert "LAB_STATUS_LONG_POLL_MS" in block
    assert "pending_finalize" in block
    assert "setInterval" in block or "setTimeout" in block
    assert "clearTimeout" in block or "clearInterval" in block
    assert "elapsed_seconds" in block


def test_poll_solver_run_status_does_not_overlap_fetches() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function pollSolverRunStatus") : js.index("const runSolverBtn")]
    assert "Promise.all" not in block
    assert "parallel" not in block.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_runtime_status_ux.py::test_poll_solver_run_status_uses_pending_finalize_timer -v`

Expected: FAIL

- [ ] **Step 3: Implement timer inside `pollSolverRunStatus`**

Replace `pollSolverRunStatus` body core with pattern below. **Keep sequential poll** — one in-flight fetch at a time.

```javascript
    function pollSolverRunStatus(statusUrl, onTerminal, onSettled) {
      const pollIntervalMs = 1500;
      const LAB_STATUS_LONG_POLL_MS = 3000;
      const runStartedAt = Date.now();
      let lastLogTail = "";

      function settlePoll() {
        if (typeof onSettled === "function") {
          onSettled();
        }
      }

      function elapsedSeconds() {
        return Math.floor((Date.now() - runStartedAt) / 1000);
      }

      function renderRunningFeedback(extra) {
        const base = {
          running: true,
          log_tail: lastLogTail,
          elapsed_seconds: elapsedSeconds(),
        };
        const merged = extra && typeof extra === "object" ? Object.assign(base, extra) : base;
        replayRunFeedback = merged;
        renderReplayRunStatus(replayRunFeedback);
      }

      function tick() {
        let longPollTimer = null;
        let elapsedTimer = null;

        function clearTimers() {
          if (longPollTimer !== null) {
            window.clearTimeout(longPollTimer);
            longPollTimer = null;
          }
          if (elapsedTimer !== null) {
            window.clearInterval(elapsedTimer);
            elapsedTimer = null;
          }
        }

        renderRunningFeedback();

        elapsedTimer = window.setInterval(function () {
          if (replayRunFeedback && replayRunFeedback.running === true) {
            renderRunningFeedback(
              replayRunFeedback.pending_finalize ? { pending_finalize: true } : null
            );
          }
        }, 1000);

        longPollTimer = window.setTimeout(function () {
          renderRunningFeedback({ pending_finalize: true });
        }, LAB_STATUS_LONG_POLL_MS);

        fetch(statusUrl, {
          method: "GET",
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            clearTimers();
            const data = bundle.data || {};
            if (typeof data.log_tail === "string" && data.log_tail) {
              lastLogTail = data.log_tail;
            }
            if (data.status === "running") {
              renderRunningFeedback();
              window.setTimeout(tick, pollIntervalMs);
              return;
            }
            try {
              onTerminal(data, bundle.res);
            } finally {
              settlePoll();
            }
          })
          .catch(function () {
            clearTimers();
            replayRunFeedback = { error_code: "network_error" };
            renderReplayRunStatus(replayRunFeedback);
            settlePoll();
          });
      }
      tick();
    }
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_runtime_status_ux.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add django_apps/web/static/web/js/asteroid_miner_layout_lab.js \
  tests/unit/asteroid_lab/test_lab_runtime_status_ux.py
git commit -m "feat(lab): elapsed and long-poll finalizing hint during status poll"
```

---

### Task 3: Status-path ingest options (disable cache warm)

**Files:**
- Modify: `django_apps/asteroid_lab/services/artifact_ingest.py`
- Modify: `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- Modify: `tests/unit/asteroid_lab/test_artifact_ingest.py`
- Modify: `tests/unit/asteroid_lab/test_reconcile_solver_run.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/asteroid_lab/test_artifact_ingest.py`:

```python
from django_apps.asteroid_lab.services.artifact_ingest import ArtifactIngestOptions


def test_ingest_with_warm_replay_cache_false_skips_compose(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="NoWarm", slug="no-warm")
    _write_artifact_with_stack_summary(tmp_path)
    with patch(
        "django_apps.asteroid_lab.services.artifact_ingest.build_lab_replay_frames_for_project",
    ) as compose_mock:
        ingest_artifact_for_project(
            project_id=int(project.pk),
            artifact_dir=tmp_path,
            ingest_options=ArtifactIngestOptions(warm_replay_cache=False),
        )
    compose_mock.assert_not_called()
```

Append to `tests/unit/asteroid_lab/test_reconcile_solver_run.py`:

```python
from unittest.mock import patch


def test_reconcile_status_path_does_not_warm_replay_cache(artifact_root: Path) -> None:
    project = m.AsteroidProject.objects.create(name="NoWarmReconcile", slug="no-warm-reconcile")
    run = _running_run(project, artifact_root)
    _write_artifact(artifact_root / run.run_key, run_key=run.run_key)

    with patch(
        "django_apps.asteroid_lab.services.artifact_ingest._warm_lab_replay_cache_after_artifact_ingest",
    ) as warm_mock:
        reconcile_solver_run(int(run.pk))

    warm_mock.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_artifact_ingest.py::test_ingest_with_warm_replay_cache_false_skips_compose -v
python -m pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py::test_reconcile_status_path_does_not_warm_replay_cache -v
```

Expected: FAIL — `ArtifactIngestOptions` or `ingest_options` not defined.

- [ ] **Step 3: Add `ArtifactIngestOptions` and wire ingest**

In `artifact_ingest.py`, after `ArtifactIngestResult`:

```python
@dataclass(frozen=True, slots=True)
class ArtifactIngestOptions:
    """Per-caller ingest behavior. Status reconcile uses the fast path."""

    warm_replay_cache: bool = True
    summarize_replay_frames: bool = True


STATUS_RECONCILE_INGEST_OPTIONS = ArtifactIngestOptions(
    warm_replay_cache=False,
    summarize_replay_frames=False,
)
```

Update `ingest_artifact_for_project` signature:

```python
def ingest_artifact_for_project(
    *,
    project_id: int,
    artifact_dir: Path,
    replace_existing_run: bool = False,
    ingest_options: ArtifactIngestOptions | None = None,
) -> ArtifactIngestResult:
```

Resolve options:

```python
    options = ingest_options or ArtifactIngestOptions()
```

Pass `summarize_replay_frames=options.summarize_replay_frames` into summary helper (Task 4).

Warm only when enabled:

```python
    if status == m.SolverRun.RunStatus.COMPLETED and options.warm_replay_cache:
        _warm_lab_replay_cache_after_artifact_ingest(
            project_id=int(project_id),
            run_id=run_id,
        )
```

Update `__all__` to export `ArtifactIngestOptions`, `STATUS_RECONCILE_INGEST_OPTIONS`.

In `solver_run_reconcile.py`:

```python
from django_apps.asteroid_lab.services.artifact_ingest import (
    STATUS_RECONCILE_INGEST_OPTIONS,
    ingest_artifact_for_project,
)
```

In `_attempt_artifact_ingest`:

```python
    ingest_artifact_for_project(
        project_id=int(run.project_id),
        artifact_dir=artifact_dir,
        replace_existing_run=True,
        ingest_options=STATUS_RECONCILE_INGEST_OPTIONS,
    )
```

- [ ] **Step 4: Run tests**

Run:

```bash
python -m pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v
python -m pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py -v
```

Expected: PASS (including existing `test_ingest_warm_compose_preserves_solver_summary_json` — default warm still on).

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/services/artifact_ingest.py \
  django_apps/asteroid_lab/services/solver_run_reconcile.py \
  tests/unit/asteroid_lab/test_artifact_ingest.py \
  tests/unit/asteroid_lab/test_reconcile_solver_run.py
git commit -m "feat(lab): status reconcile ingest skips replay cache warm"
```

---

### Task 4: O(1) manifest summary on status hot path

**Files:**
- Modify: `django_apps/asteroid_lab/services/artifact_ingest.py`
- Modify: `tests/unit/asteroid_lab/test_artifact_ingest.py`

- [ ] **Step 1: Write the failing test**

```python
from unittest.mock import patch

import django_apps.asteroid_lab.services.artifact_ingest as ingest_mod


def test_ingest_fast_summary_does_not_iterate_replay_core(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="FastSummary", slug="fast-summary")
    _write_artifact(tmp_path)

    with patch.object(ingest_mod, "iter_replay_core_frames") as iter_mock:
        result = ingest_artifact_for_project(
            project_id=int(project.pk),
            artifact_dir=tmp_path,
            ingest_options=ArtifactIngestOptions(summarize_replay_frames=False),
        )

    iter_mock.assert_not_called()
    summary = result.solver_run.lab_replay_manifest_summary_json
    assert summary["frame_count"] == 0
    assert summary["preview_frame_index"] == 0
    assert summary["mode"] == "artifact_jsonl"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/asteroid_lab/test_artifact_ingest.py::test_ingest_fast_summary_does_not_iterate_replay_core -v`

Expected: FAIL — `iter_replay_core_frames` still called.

- [ ] **Step 3: Implement bounded summary**

Change `_lab_replay_manifest_summary` signature:

```python
def _lab_replay_manifest_summary(
    *,
    artifact_dir: Path,
    manifest: ArtifactManifestRecord,
    summarize_replay_frames: bool = True,
) -> dict[str, Any]:
    replay_path = _manifest_path(artifact_dir, manifest, "replay_core")
    frame_count = 0
    preview_frame_index = 0
    if summarize_replay_frames and replay_path is not None and replay_path.is_file():
        for _frame in iter_replay_core_frames(replay_path):
            frame_count += 1
        if frame_count:
            preview_frame_index = frame_count - 1
    return {
        "mode": "artifact_jsonl",
        "replay_payload_version": LAB_REPLAY_PAYLOAD_VERSION,
        "lab_replay_cache_schema_version": CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION,
        "artifact_run_key": manifest.run_key,
        "replay_core_path": str(replay_path) if replay_path is not None else "",
        "frame_count": frame_count,
        "preview_frame_index": preview_frame_index,
        "preview_frame": None,
        "replay_track_metrics": {},
    }
```

Call site in `ingest_artifact_for_project`:

```python
        run.lab_replay_manifest_summary_json = _lab_replay_manifest_summary(
            artifact_dir=Path(artifact_dir),
            manifest=manifest,
            summarize_replay_frames=options.summarize_replay_frames,
        )
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`

Expected: PASS — default path still sets `frame_count == 1` in `test_ingest_artifact_writes_index_only_solver_run`.

- [ ] **Step 5: Commit**

```bash
git add django_apps/asteroid_lab/services/artifact_ingest.py \
  tests/unit/asteroid_lab/test_artifact_ingest.py
git commit -m "feat(lab): O(1) replay manifest summary on status ingest path"
```

---

### Task 5: Regression — no compose/cache warm from status integration

**Files:**
- Modify: `tests/integration/web/test_asteroid_miner_layout_solver_async.py`

- [ ] **Step 1: Write the failing integration test**

```python
from unittest.mock import patch


@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_http_status_complete_does_not_warm_replay_cache(
    client: Client, tmp_path, settings
) -> None:
    settings.ASTEROID_LAB_ARTIFACT_ROOT = tmp_path
    slug = "async-no-warm"
    project = m.AsteroidProject.objects.create(name="Async No Warm", slug=slug)
    m.AsteroidMapInput.objects.create(project=project, copy_code=_unique_valid_copy())

    def fake_spawn(request, **kwargs):
        del kwargs
        return SolverSubprocessSpawnResult(
            run_key=request.run_key,
            artifact_dir=tmp_path / request.run_key,
            sidecar_log_path=tmp_path / ".subprocess_logs" / f"{request.run_key}.log",
            handle=SimpleNamespace(pid=9999),
        )

    with patch(
        "django_apps.asteroid_lab.services.solver_runtime_entry.spawn_solver_subprocess_detached",
        side_effect=fake_spawn,
    ):
        with patch(
            "django_apps.web.views.public_pages.build_asteroid_game_data_snapshot_with_provenance",
            return_value=SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
        ):
            with patch(
                "django_apps.web.views.public_pages.build_game_data_snapshot_payload",
                return_value={"schema_version": 1},
            ):
                post = client.post(
                    reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
                    data={},
                    content_type="application/json",
                )

    status_url = post.json()["status_url"]
    _write_artifact(tmp_path / post.json()["run_key"], run_key=post.json()["run_key"])

    with patch(
        "django_apps.asteroid_lab.services.artifact_ingest.build_lab_replay_frames_for_project",
    ) as compose_mock:
        status = client.get(status_url)

    compose_mock.assert_not_called()
    assert status.status_code == 200
    assert status.json()["status"] == m.SolverRun.RunStatus.COMPLETED
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/integration/web/test_asteroid_miner_layout_solver_async.py::test_http_status_complete_does_not_warm_replay_cache -v`

Expected: PASS after Tasks 3–4 (may FAIL before).

- [ ] **Step 3: Commit**

```bash
git add tests/integration/web/test_asteroid_miner_layout_solver_async.py
git commit -m "test(lab): status complete must not compose replay cache"
```

---

### Task 6: Measure before/after latency and document

**Files:**
- Create: `docs/superpowers/reports/2026-06-10-runtime-status-c1-latency.md`

- [ ] **Step 1: Capture baseline (if not already noted)**

Manual or scripted timing on a representative project run. Record in report:

```text
Before C1 (from user network capture):
  running status/: 14–22 ms, 0.6 kB
  final status/:   ~50.38 s, 2.1 kB
  lab-replay/:     ~892 ms, 255 kB
```

- [ ] **Step 2: After C1 deploy locally, measure three metrics**

Use browser Network tab or a small script hitting:

1. `GET .../status/` while `running` (10+ samples → p99)
2. `GET .../status/` on completion ingest poll (p99 + max)
3. First `GET .../lab-replay/` after completion (p99 + max)

Example helper (optional Django shell / curl loop) — document actual commands used.

- [ ] **Step 3: Write report**

Create `docs/superpowers/reports/2026-06-10-runtime-status-c1-latency.md`:

```markdown
# Runtime Status C1 Latency Report (2026-06-10)

## Environment
- Branch: ...
- Fixture/project slug: ...
- Artifact size (replay_core lines): ...

## Results

| Metric | Before | After C1 | Notes |
|--------|--------|----------|-------|
| running status/ p99 | ~20 ms | | target <100 ms |
| final status/ p99 | ~50 s | | meaningful reduction required |
| final status/ max | ~50 s | | |
| first lab-replay/ p99 | ~892 ms | | may increase; document separately |

## Conclusion
- C2 needed? yes/no — if final status/ p99 still >500 ms, open C2 plan.
```

- [ ] **Step 4: Run validation gates**

```bash
python manage.py check
powershell -File scripts/test_fast.ps1
python -m pytest tests/unit/asteroid_lab/test_lab_runtime_status_ux.py \
  tests/unit/asteroid_lab/test_artifact_ingest.py \
  tests/unit/asteroid_lab/test_reconcile_solver_run.py \
  tests/integration/web/test_asteroid_miner_layout_solver_async.py -v
ruff check django_apps/asteroid_lab/services/artifact_ingest.py django_apps/asteroid_lab/services/solver_run_reconcile.py
mypy django_apps/asteroid_lab/services/artifact_ingest.py django_apps/asteroid_lab/services/solver_run_reconcile.py
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/reports/2026-06-10-runtime-status-c1-latency.md
git commit -m "docs(lab): C1 runtime status latency measurements"
```

---

## Plan self-review

| Spec requirement | Task |
|------------------|------|
| UI log_tail textContent, cap, in-flight preserve | Task 1–2 |
| Long-poll timer before await resolves | Task 2 |
| No overlapping polls | Task 2 (sequential fetch preserved) |
| Status-path only: no cache warm | Task 3 |
| O(1) summary, no JSONL scan on hot path | Task 4 |
| Offline ingest keeps warm default | Task 3 (`ArtifactIngestOptions` default) |
| Regression tests | Tasks 3–5 |
| Three latency metrics documented | Task 6 |
| No SSE/progress.jsonl/phase/live replay | C1 scope guard |
| lab-replay sole compose path | Unchanged endpoint |

No placeholders remain. Type names consistent: `ArtifactIngestOptions`, `STATUS_RECONCILE_INGEST_OPTIONS`, `summarize_replay_frames`, `warm_replay_cache`.

---

## C2 trigger (do not implement in C1)

If Task 6 shows final `status/` p99 still > 500 ms, follow spec C2: `phase`, `replay_ready`, deferred ingest off status thread.

`replay_ready=true` means only that `lab-replay/` may be requested — not cache exists or frames pre-composed.
